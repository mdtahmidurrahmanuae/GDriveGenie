import asyncio
import io
import logging
import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import PBClient, get_pb
from models.models import DriveAccount, File
from services.auth_service import verify_token
from services.drive_service import (
    delete_drive_file,
    stream_file,
    list_shared_files,
    list_shared_folder_children,
    list_trash_files,
    move_file,
    pick_best_account,
    remove_shared_file,
    rename_file,
    restore_file,
    share_file,
    sync_files_from_drives,
    trash_drive_file,
    unshare_file,
    upload_file,
)
from services.sort_service import sort_all_drives as _sort_all_drives

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["files"])


class RenameRequest(BaseModel):
    new_name: str


class MoveRequest(BaseModel):
    new_parent_drive_file_id: str


def _file_to_dict(f: File, account_email: str | None = None) -> dict:
    return {
        "id": f.id,
        "file_name": f.file_name,
        "drive_file_id": f.drive_file_id,
        "account_id": f.account_id,
        "account_index": f.account_index,
        "account_email": account_email,
        "size": f.size,
        "mime_type": f.mime_type,
        "has_thumbnail": f.thumbnail_link is not None,
        "parent_drive_file_id": f.parent_drive_file_id,
        "created_at": f.drive_created_at,
    }


async def _get_file_and_account(file_id: str, user_id: str, pb: PBClient):
    """Fetch file + account, enforcing user ownership."""
    try:
        row = await pb.get_record("gdrive_files", file_id)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
    if row.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    account_id = row.get("account", "")
    acc_rows = await pb.list_records(
        "gdrive_accounts", filter=f'id="{account_id}"', per_page=1
    )
    if not acc_rows:
        raise HTTPException(status_code=404, detail="Account not found")
    acc_row = acc_rows[0]
    account = DriveAccount.from_pb(acc_row)
    file = File.from_pb(row, account_index=account.account_index)
    return file, account


@router.post("/sync")
async def sync_files(
    background_tasks: BackgroundTasks,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]

    async def _sync_bg():
        from services.pb_client import PBClient as _PB
        bg_pb = _PB()
        try:
            await sync_files_from_drives(bg_pb, user_id)
        finally:
            await bg_pb.aclose()

    background_tasks.add_task(asyncio.run, _sync_bg())
    return {"ok": True}


@router.get("/search")
async def search_files(
    q: str = "",
    account_id: str | None = None,
    mime_type: str | None = None,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    conditions = [f'user="{user_id}"']
    if q:
        # PocketBase filter: case-insensitive contains
        conditions.append(f'file_name~"{q}"')
    if account_id:
        conditions.append(f'account="{account_id}"')
    if mime_type:
        conditions.append(f'mime_type~"{mime_type}"')

    filter_str = " && ".join(conditions)
    rows = await pb.list_records(
        "gdrive_files", filter=filter_str, sort="-drive_created_at", per_page=500
    )

    # Build account index map
    acc_rows = await pb.list_records(
        "gdrive_accounts", filter=f'user="{user_id}" && is_connected=true'
    )
    acc_map = {r["id"]: r for r in acc_rows}

    result = []
    for row in rows:
        acc_row = acc_map.get(row.get("account", ""), {})
        account = DriveAccount.from_pb(acc_row) if acc_row else None
        f = File.from_pb(row, account_index=account.account_index if account else 0)
        result.append(_file_to_dict(f, acc_row.get("email") if acc_row else None))
    return result


@router.get("")
async def list_files(
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    rows = await pb.list_records(
        "gdrive_files",
        filter=f'user="{user_id}"',
        sort="-drive_created_at",
        per_page=2000,
    )
    acc_rows = await pb.list_records(
        "gdrive_accounts", filter=f'user="{user_id}" && is_connected=true'
    )
    acc_map = {r["id"]: r for r in acc_rows}

    result = []
    for row in rows:
        acc_row = acc_map.get(row.get("account", ""), {})
        account = DriveAccount.from_pb(acc_row) if acc_row else None
        f = File.from_pb(row, account_index=account.account_index if account else 0)
        result.append(_file_to_dict(f, acc_row.get("email") if acc_row else None))
    return result


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile,
    parent_folder_id: str | None = Form(None),    # virtual folder PB id (optional)
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    storage_limit = token.get("storage_limit_bytes", 16106127360)

    # Check user's storage
    user_rec = await pb.get_record("gdrive_users", user_id)
    used = int(user_rec.get("storage_used_bytes") or 0)
    limit = int(user_rec.get("storage_limit_bytes") or storage_limit)

    best_acc_id = await pick_best_account(pb, user_id)
    if best_acc_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No connected Drive accounts with available space",
        )

    acc_row = await pb.get_record("gdrive_accounts", best_acc_id)
    account = DriveAccount.from_pb(acc_row)

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    content = await file.read()
    file_size = len(content)

    if used + file_size > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Storage limit reached ({limit // (1024**3)} GB). Contact admin to increase your quota.",
        )

    result = upload_file(account, io.BytesIO(content), file.filename, mime_type)

    new_file = await pb.create_record("gdrive_files", {
        "user": user_id,
        "account": best_acc_id,
        "file_name": file.filename,
        "drive_file_id": result["drive_file_id"],
        "size": result["size"],
        "mime_type": result["mime_type"],
        "thumbnail_link": result.get("thumbnail_link"),
        "parent_drive_file_id": result.get("parent_drive_file_id"),
    })

    # Update storage_used_bytes
    try:
        await pb.update_record("gdrive_users", user_id, {
            "storage_used_bytes": used + result["size"],
        })
    except Exception:
        pass

    # If a virtual folder was specified, add the mapping
    if parent_folder_id:
        try:
            # Verify folder belongs to this user
            folder_rec = await pb.get_record("gdrive_folders", parent_folder_id)
            if folder_rec.get("user") == user_id:
                await pb.create_record("gdrive_folder_files", {
                    "folder": parent_folder_id,
                    "file": new_file["id"],
                })
        except Exception:
            pass

    # Auto-sort: move the newly uploaded file into its MIME-type folder in background
    async def _auto_sort():
        from services.pb_client import PBClient as _PB
        bg_pb = _PB()
        try:
            await _sort_all_drives(bg_pb, user_id)
        except Exception:
            pass
        finally:
            await bg_pb.aclose()

    background_tasks.add_task(asyncio.run, _auto_sort())

    f = File.from_pb(new_file, account_index=account.account_index)
    return _file_to_dict(f, account.email)


@router.get("/{file_id}/download")
async def get_download(
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, file.drive_file_id),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file.file_name}"'},
    )


@router.get("/{file_id}/view")
async def get_view(
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, file.drive_file_id),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{file.file_name}"'},
    )


@router.patch("/{file_id}/rename")
async def rename(
    file_id: str,
    body: RenameRequest,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    rename_file(account, file.drive_file_id, body.new_name)
    updated = await pb.update_record("gdrive_files", file_id, {"file_name": body.new_name})
    f = File.from_pb(updated, account_index=account.account_index)
    return _file_to_dict(f, account.email)


@router.patch("/{file_id}/move")
async def move_file_route(
    file_id: str,
    body: MoveRequest,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    try:
        move_file(account, file.drive_file_id, body.new_parent_drive_file_id, file.parent_drive_file_id)
    except Exception as e:
        logger.exception("move_file failed for file_id=%s", file_id)
        raise HTTPException(status_code=503, detail=str(e))
    new_parent = None if body.new_parent_drive_file_id == "root" else body.new_parent_drive_file_id
    updated = await pb.update_record("gdrive_files", file_id, {"parent_drive_file_id": new_parent})
    f = File.from_pb(updated, account_index=account.account_index)
    return _file_to_dict(f, account.email)


@router.post("/{file_id}/share")
async def share_file_route(
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        link = share_file(account, file.drive_file_id)
        return {"link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_file_route(
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, token["sub"], pb)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        unshare_file(account, file.drive_file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    file, account = await _get_file_and_account(file_id, user_id, pb)
    if account.is_connected:
        try:
            trash_drive_file(account, file.drive_file_id)
        except Exception:
            pass

    # Update storage
    try:
        user_rec = await pb.get_record("gdrive_users", user_id)
        used = int(user_rec.get("storage_used_bytes") or 0)
        new_used = max(0, used - file.size)
        await pb.update_record("gdrive_users", user_id, {"storage_used_bytes": new_used})
    except Exception:
        pass

    # Remove folder mappings
    try:
        mappings = await pb.list_records("gdrive_folder_files", filter=f'file="{file_id}"')
        for m in mappings:
            await pb.delete_record("gdrive_folder_files", m["id"])
    except Exception:
        pass

    await pb.delete_record("gdrive_files", file_id)


# ---------------------------------------------------------------------------
# Shared files (Google Drive "Shared with me")
# ---------------------------------------------------------------------------

@router.get("/shared")
async def list_shared(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    acc_rows = await pb.list_records(
        "gdrive_accounts", filter=f'user="{user_id}" && is_connected=true'
    )
    results = []
    for row in acc_rows:
        try:
            results.extend(list_shared_files(DriveAccount.from_pb(row)))
        except Exception:
            pass
    return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)


@router.get("/shared/{account_id}/{folder_id}/children")
async def list_shared_children(
    account_id: str, folder_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_row = await pb.get_record("gdrive_accounts", account_id)
    if acc_row.get("user") != user_id:
        raise HTTPException(status_code=403)
    account = DriveAccount.from_pb(acc_row)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        return list_shared_folder_children(account, folder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shared/{account_id}/{drive_file_id}/download")
async def download_shared_file(
    account_id: str, drive_file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_row = await pb.get_record("gdrive_accounts", account_id)
    if acc_row.get("user") != user_id:
        raise HTTPException(status_code=403)
    account = DriveAccount.from_pb(acc_row)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, drive_file_id),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{drive_file_id}"'},
    )


@router.delete("/shared/{account_id}/{drive_file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shared_file(
    account_id: str, drive_file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_row = await pb.get_record("gdrive_accounts", account_id)
    if acc_row.get("user") != user_id:
        raise HTTPException(status_code=403)
    account = DriveAccount.from_pb(acc_row)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        remove_shared_file(account, drive_file_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Trash
# ---------------------------------------------------------------------------

@router.get("/trash")
async def list_trash(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    acc_rows = await pb.list_records(
        "gdrive_accounts", filter=f'user="{user_id}" && is_connected=true'
    )
    results = []
    for row in acc_rows:
        try:
            results.extend(list_trash_files(DriveAccount.from_pb(row)))
        except Exception:
            pass
    return sorted(results, key=lambda x: x.get("trashed_at", ""), reverse=True)


@router.post("/trash/{account_id}/{drive_file_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_trash_file(
    account_id: str, drive_file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_row = await pb.get_record("gdrive_accounts", account_id)
    if acc_row.get("user") != user_id:
        raise HTTPException(status_code=403)
    try:
        restore_file(DriveAccount.from_pb(acc_row), drive_file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trash/{account_id}/{drive_file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trash_file(
    account_id: str, drive_file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_row = await pb.get_record("gdrive_accounts", account_id)
    if acc_row.get("user") != user_id:
        raise HTTPException(status_code=403)
    try:
        delete_drive_file(DriveAccount.from_pb(acc_row), drive_file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
