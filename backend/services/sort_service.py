import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from googleapiclient.errors import HttpError

from models.models import DriveAccount
from services.drive_service import _retry_on_rate_limit, build_service
from services.pb_client import PBClient

logger = logging.getLogger(__name__)

MIME_TYPE_FOLDERS: dict[str, list[str]] = {
    "Documents": [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "application/rtf",
        "application/vnd.oasis.opendocument.text",
    ],
    "Spreadsheets": [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/vnd.oasis.opendocument.spreadsheet",
    ],
    "PDFs": [
        "application/pdf",
    ],
    "Presentations": [
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.oasis.opendocument.presentation",
    ],
    "Archives": [
        "application/zip",
        "application/x-rar-compressed",
        "application/x-7z-compressed",
        "application/gzip",
        "application/x-tar",
    ],
    "Code": [
        "text/x-python",
        "application/javascript",
        "text/html",
        "text/css",
        "application/json",
        "application/xml",
    ],
    # Wildcard categories — checked by prefix
    "Images": ["image/"],
    "Videos": ["video/"],
    "Audio": ["audio/"],
}

# Build a flat exact-match lookup for fast classification
_EXACT: dict[str, str] = {}
_PREFIX: list[tuple[str, str]] = []

for folder_name, types in MIME_TYPE_FOLDERS.items():
    for mime in types:
        if mime.endswith("/"):
            _PREFIX.append((mime, folder_name))
        else:
            _EXACT[mime] = folder_name

# Folders we manage — never move these
_SORT_FOLDER_NAMES = set(MIME_TYPE_FOLDERS.keys()) | {"Other"}

# Google Drive folder MIME type
_FOLDER_MIME = "application/vnd.google-apps.folder"


def classify_file(mime_type: str | None) -> str:
    """Return the destination folder name for a given MIME type."""
    if not mime_type:
        return "Other"
    exact = _EXACT.get(mime_type)
    if exact:
        return exact
    for prefix, folder_name in _PREFIX:
        if mime_type.startswith(prefix):
            return folder_name
    return "Other"


def get_or_create_sort_folder(account: DriveAccount, folder_name: str) -> str:
    """Return the Drive folder ID for `folder_name`, creating it if needed."""
    service = build_service(account)
    safe_name = folder_name.replace("'", "\\'")
    query = (
        f"name='{safe_name}' and mimeType='{_FOLDER_MIME}' and trashed=false"
        " and 'root' in parents"
    )
    result = _retry_on_rate_limit(service.files().list(q=query, fields="files(id)").execute)
    existing = result.get("files", [])
    if existing:
        return existing[0]["id"]
    folder = _retry_on_rate_limit(
        service.files()
        .create(
            body={"name": folder_name, "mimeType": _FOLDER_MIME},
            fields="id",
        )
        .execute
    )
    return folder["id"]


def sort_files_for_account(account: DriveAccount) -> dict:
    """
    Sort all non-folder, non-trashed files owned by this account into
    MIME-type-based folders at Drive root.

    Returns:
        {moved: int, skipped: int, errors: int, by_folder: {folder_name: int}}
    """
    service = build_service(account)

    # List all owned, non-trashed files (not folders)
    items: list[dict] = []
    page_token = None
    while True:
        kwargs: dict = {
            "q": (
                f"'me' in owners and trashed = false"
                f" and mimeType != '{_FOLDER_MIME}'"
            ),
            "pageSize": 1000,
            "fields": "nextPageToken, files(id, name, mimeType, parents)",
        }
        if page_token:
            kwargs["pageToken"] = page_token
        result = _retry_on_rate_limit(service.files().list(**kwargs).execute)
        items.extend(result.get("files", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    # Cache folder IDs we've already looked up / created
    folder_id_cache: dict[str, str] = {}

    # We need root's Drive ID to detect files already at root
    try:
        root_meta = _retry_on_rate_limit(service.files().get(fileId="root", fields="id").execute)
        root_id = root_meta.get("id")
    except Exception:
        root_id = None

    stats: dict = {"moved": 0, "skipped": 0, "errors": 0, "by_folder": {}}

    # Collect sort folder IDs to know if a file is already in one
    # We'll lazily populate this as we encounter files in sort folders.
    sort_folder_ids: dict[str, str] = {}  # folder_name -> drive_folder_id

    def _sort_folder_id(name: str) -> str:
        if name not in folder_id_cache:
            fid = get_or_create_sort_folder(account, name)
            folder_id_cache[name] = fid
            sort_folder_ids[name] = fid
        return folder_id_cache[name]

    # Build reverse map: drive_id -> folder_name (populated as we create/fetch)
    _id_to_name: dict[str, str] = {}

    for item in items:
        drive_file_id: str = item["id"]
        mime_type: str = item.get("mimeType", "")
        current_parents: list[str] = item.get("parents", [])

        target_name = classify_file(mime_type)
        target_id = _sort_folder_id(target_name)

        # Update reverse map
        _id_to_name[target_id] = target_name

        # Skip if already in the correct sort folder
        if target_id in current_parents:
            stats["skipped"] += 1
            continue

        # Determine remove_parents
        if current_parents:
            remove_parents = ",".join(current_parents)
        elif root_id:
            remove_parents = root_id
        else:
            stats["errors"] += 1
            continue

        try:
            _retry_on_rate_limit(
                service.files()
                .update(
                    fileId=drive_file_id,
                    addParents=target_id,
                    removeParents=remove_parents,
                    fields="id",
                )
                .execute
            )
            stats["moved"] += 1
            stats["by_folder"][target_name] = stats["by_folder"].get(target_name, 0) + 1
        except HttpError as e:
            logger.warning("sort: move failed for %s: %s", drive_file_id, e)
            stats["errors"] += 1

    return stats


async def sort_all_drives(pb: PBClient, user_id: str) -> list[dict]:
    """
    Sort files for every connected account belonging to user_id.
    Returns a list of per-account result dicts.
    """
    account_rows = await pb.list_records(
        "gdrive_accounts",
        filter=f'user="{user_id}" && is_connected=true',
    )
    accounts = [DriveAccount.from_pb(r) for r in account_rows]

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, len(accounts))) as executor:
        futures = {executor.submit(sort_files_for_account, acc): acc for acc in accounts}
        for future in as_completed(futures):
            acc = futures[future]
            try:
                stats = future.result()
            except Exception as e:
                logger.exception("sort_files_for_account failed for account %s", acc.id)
                stats = {"moved": 0, "skipped": 0, "errors": 1, "by_folder": {}, "error": str(e)}
            results.append({
                "account_id": acc.id,
                "account_index": acc.account_index,
                "email": acc.email,
                **stats,
            })

    return sorted(results, key=lambda x: x["account_index"])
