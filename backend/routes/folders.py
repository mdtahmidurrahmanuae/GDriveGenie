"""Virtual folder management — folders live in PocketBase, files stay in Google Drive."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from database import PBClient, get_pb
from models.models import Folder
from services.auth_service import verify_token

router = APIRouter(prefix="/folders", tags=["folders"])


class FolderCreate(BaseModel):
    name: str
    parent_id: str | None = None


class FolderRename(BaseModel):
    name: str


@router.get("")
async def list_folders(
    parent_id: str | None = None,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    if parent_id:
        filter_str = f'user="{user_id}" && parent="{parent_id}"'
    else:
        # Root-level folders (no parent)
        filter_str = f'user="{user_id}" && parent=""'
    rows = await pb.list_records("gdrive_folders", filter=filter_str, sort="name")
    return [_folder_to_dict(Folder.from_pb(r)) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")

    # Validate parent belongs to this user
    if body.parent_id:
        parent = await pb.get_record("gdrive_folders", body.parent_id)
        if parent.get("user") != user_id:
            raise HTTPException(status_code=403, detail="Parent folder not found")

    data: dict = {"user": user_id, "name": body.name.strip()}
    if body.parent_id:
        data["parent"] = body.parent_id

    row = await pb.create_record("gdrive_folders", data)
    return _folder_to_dict(Folder.from_pb(row))


@router.get("/{folder_id}")
async def get_folder(
    folder_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    row = await pb.get_record("gdrive_folders", folder_id)
    if row.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _folder_to_dict(Folder.from_pb(row))


@router.patch("/{folder_id}")
async def rename_folder(
    folder_id: str,
    body: FolderRename,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    row = await pb.get_record("gdrive_folders", folder_id)
    if row.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Folder name cannot be empty")
    updated = await pb.update_record("gdrive_folders", folder_id, {"name": body.name.strip()})
    return _folder_to_dict(Folder.from_pb(updated))


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    row = await pb.get_record("gdrive_folders", folder_id)
    if row.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete child folders recursively
    await _delete_folder_recursive(pb, folder_id, user_id)


async def _delete_folder_recursive(pb: PBClient, folder_id: str, user_id: str):
    """Delete folder, its file mappings, its shares, and child folders."""
    # Delete file mappings
    mappings = await pb.list_records("gdrive_folder_files", filter=f'folder="{folder_id}"', per_page=2000)
    for m in mappings:
        try:
            await pb.delete_record("gdrive_folder_files", m["id"])
        except Exception:
            pass

    # Delete shares for this folder
    shares = await pb.list_records("gdrive_shares", filter=f'folder="{folder_id}"', per_page=500)
    for s in shares:
        try:
            await pb.delete_record("gdrive_shares", s["id"])
        except Exception:
            pass

    # Recurse into children
    children = await pb.list_records(
        "gdrive_folders", filter=f'user="{user_id}" && parent="{folder_id}"', per_page=500
    )
    for child in children:
        await _delete_folder_recursive(pb, child["id"], user_id)

    await pb.delete_record("gdrive_folders", folder_id)


# ---------------------------------------------------------------------------
# Files within a folder
# ---------------------------------------------------------------------------

@router.get("/{folder_id}/files")
async def list_folder_files(
    folder_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    row = await pb.get_record("gdrive_folders", folder_id)
    if row.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    mappings = await pb.list_records(
        "gdrive_folder_files", filter=f'folder="{folder_id}"', per_page=2000, expand="file"
    )
    files = []
    for m in mappings:
        file_rec = m.get("expand", {}).get("file") or {}
        if file_rec:
            files.append({
                "id": file_rec["id"],
                "file_name": file_rec.get("file_name", ""),
                "drive_file_id": file_rec.get("drive_file_id", ""),
                "account_id": file_rec.get("account", ""),
                "size": file_rec.get("size", 0),
                "mime_type": file_rec.get("mime_type"),
                "has_thumbnail": bool(file_rec.get("thumbnail_link")),
                "created_at": file_rec.get("drive_created_at", ""),
            })
    return files


@router.post("/{folder_id}/files/{file_id}", status_code=status.HTTP_201_CREATED)
async def add_file_to_folder(
    folder_id: str,
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    folder_row = await pb.get_record("gdrive_folders", folder_id)
    if folder_row.get("user") != user_id:
        raise HTTPException(status_code=403)

    file_row = await pb.get_record("gdrive_files", file_id)
    if file_row.get("user") != user_id:
        raise HTTPException(status_code=403)

    # Check not already mapped
    existing = await pb.list_records(
        "gdrive_folder_files",
        filter=f'folder="{folder_id}" && file="{file_id}"',
        per_page=1,
    )
    if existing:
        return {"ok": True, "already_exists": True}

    await pb.create_record("gdrive_folder_files", {"folder": folder_id, "file": file_id})
    return {"ok": True}


@router.delete("/{folder_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_file_from_folder(
    folder_id: str,
    file_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    folder_row = await pb.get_record("gdrive_folders", folder_id)
    if folder_row.get("user") != user_id:
        raise HTTPException(status_code=403)

    mappings = await pb.list_records(
        "gdrive_folder_files",
        filter=f'folder="{folder_id}" && file="{file_id}"',
    )
    for m in mappings:
        await pb.delete_record("gdrive_folder_files", m["id"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _folder_to_dict(f: Folder) -> dict:
    return {
        "id": f.id,
        "name": f.name,
        "parent_id": f.parent_id,
        "created": f.created,
    }
