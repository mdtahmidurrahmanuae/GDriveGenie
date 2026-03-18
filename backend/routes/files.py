import asyncio
import io
import logging
import mimetypes

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_d1
from models.models import DriveAccount, File
from services.auth_service import verify_token
from services.d1_client import D1Client
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
        "account_index": f.account_index,
        "account_email": account_email,
        "size": f.size,
        "mime_type": f.mime_type,
        "has_thumbnail": f.thumbnail_link is not None,
        "parent_drive_file_id": f.parent_drive_file_id,
        "created_at": f.created_at,  # already a string from D1
    }


async def _get_file_and_account(file_id: int, d1: D1Client):
    rows = await d1.execute("SELECT * FROM files WHERE id = ?", [file_id])
    if not rows:
        raise HTTPException(status_code=404, detail="File not found")
    file = File.from_row(rows[0])
    acc_rows = await d1.execute(
        "SELECT * FROM drive_accounts WHERE account_index = ?", [file.account_index]
    )
    account = DriveAccount.from_row(acc_rows[0]) if acc_rows else None
    return file, account


@router.post("/sync")
async def sync_files(background_tasks: BackgroundTasks, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    async def _sync_bg() -> None:
        from services.d1_client import D1Client as _D1Client
        bg_d1 = _D1Client()
        try:
            await sync_files_from_drives(bg_d1)
        finally:
            await bg_d1.aclose()

    background_tasks.add_task(asyncio.run, _sync_bg())
    return {"ok": True}


@router.get("/search")
async def search_files(
    q: str = "",
    account_index: int | None = None,
    mime_type: str | None = None,
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    acc_rows = await d1.execute("SELECT account_index, email FROM drive_accounts WHERE is_connected = 1")
    connected_indices = [r["account_index"] for r in acc_rows]
    email_map = {r["account_index"]: r.get("email") for r in acc_rows}
    if not connected_indices:
        return []

    placeholders = ",".join("?" * len(connected_indices))
    conditions = [f"account_index IN ({placeholders})"]
    params: list = list(connected_indices)

    if q:
        conditions.append("LOWER(file_name) LIKE LOWER(?)")
        params.append(f"%{q}%")
    if account_index is not None and account_index in connected_indices:
        conditions.append("account_index = ?")
        params.append(account_index)
    if mime_type:
        conditions.append("mime_type LIKE ?")
        params.append(f"%{mime_type}%")

    where = " AND ".join(conditions)
    rows = await d1.execute(
        f"SELECT * FROM files WHERE {where} ORDER BY created_at DESC LIMIT 500",
        params,
    )
    return [_file_to_dict(File.from_row(r), email_map.get(r["account_index"])) for r in rows]


@router.get("")
async def list_files(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    acc_rows = await d1.execute("SELECT account_index, email FROM drive_accounts WHERE is_connected = 1")
    connected_indices = [r["account_index"] for r in acc_rows]
    email_map = {r["account_index"]: r.get("email") for r in acc_rows}
    if not connected_indices:
        return []
    placeholders = ",".join("?" * len(connected_indices))
    file_rows = await d1.execute(
        f"SELECT * FROM files WHERE account_index IN ({placeholders}) ORDER BY created_at DESC",
        connected_indices,
    )
    return [_file_to_dict(File.from_row(r), email_map.get(r["account_index"])) for r in file_rows]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile,
    parent_folder_id: str | None = Form(None),
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    best_index = await pick_best_account(d1)
    if best_index is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No connected Drive accounts with available space",
        )

    acc_rows = await d1.execute(
        "SELECT * FROM drive_accounts WHERE account_index = ?", [best_index]
    )
    if not acc_rows:
        raise HTTPException(status_code=503, detail="Account not found")
    account = DriveAccount.from_row(acc_rows[0])

    mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    content = await file.read()
    stream = io.BytesIO(content)

    result = upload_file(account, stream, file.filename, mime_type, parent_folder_id or None)

    await d1.execute(
        "INSERT INTO files (file_name, drive_file_id, account_index, size, mime_type, "
        "thumbnail_link, parent_drive_file_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            file.filename,
            result["drive_file_id"],
            best_index,
            result["size"],
            result["mime_type"],
            result.get("thumbnail_link"),
            result.get("parent_drive_file_id"),
        ],
    )
    id_rows = await d1.execute("SELECT last_insert_rowid() AS id")
    new_id = id_rows[0]["id"]

    new_rows = await d1.execute("SELECT * FROM files WHERE id = ?", [new_id])
    return _file_to_dict(File.from_row(new_rows[0]))


@router.get("/{file_id}/download")
async def get_download(file_id: int, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    file, account = await _get_file_and_account(file_id, d1)
    if not account or not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, file.drive_file_id),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file.file_name}"'},
    )


@router.get("/{file_id}/view")
async def get_view(file_id: int, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    file, account = await _get_file_and_account(file_id, d1)
    if not account or not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, file.drive_file_id),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{file.file_name}"'},
    )


@router.patch("/{file_id}/rename")
async def rename(
    file_id: int,
    body: RenameRequest,
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, d1)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    rename_file(account, file.drive_file_id, body.new_name)
    await d1.execute("UPDATE files SET file_name = ? WHERE id = ?", [body.new_name, file_id])
    updated_rows = await d1.execute("SELECT * FROM files WHERE id = ?", [file_id])
    return _file_to_dict(File.from_row(updated_rows[0]))


@router.patch("/{file_id}/move")
async def move_file_route(
    file_id: int,
    body: MoveRequest,
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    file, account = await _get_file_and_account(file_id, d1)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    try:
        move_file(account, file.drive_file_id, body.new_parent_drive_file_id, file.parent_drive_file_id)
    except Exception as e:
        logger.exception("move_file failed for file_id=%s", file_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    new_parent = None if body.new_parent_drive_file_id == "root" else body.new_parent_drive_file_id
    await d1.execute("UPDATE files SET parent_drive_file_id = ? WHERE id = ?", [new_parent, file_id])
    updated_rows = await d1.execute("SELECT * FROM files WHERE id = ?", [file_id])
    return _file_to_dict(File.from_row(updated_rows[0]))


@router.post("/{file_id}/share")
async def share_file_route(file_id: int, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    file, account = await _get_file_and_account(file_id, d1)
    if not account or not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        link = share_file(account, file.drive_file_id)
        return {"link": link}
    except Exception as e:
        logger.exception("share_file failed for file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_file_route(file_id: int, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    file, account = await _get_file_and_account(file_id, d1)
    if not account or not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        unshare_file(account, file.drive_file_id)
    except Exception as e:
        logger.exception("unshare_file failed for file_id=%s", file_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: int, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    file, account = await _get_file_and_account(file_id, d1)
    if account and account.is_connected:
        try:
            trash_drive_file(account, file.drive_file_id)
        except Exception:
            pass
    await d1.execute("DELETE FROM files WHERE id = ?", [file_id])


@router.get("/shared/{account_index}/{drive_file_id}/download")
async def download_shared_file(account_index: int, drive_file_id: str, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM drive_accounts WHERE account_index = ?", [account_index])
    if not rows:
        raise HTTPException(status_code=503, detail="Account not connected")
    account = DriveAccount.from_row(rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    return StreamingResponse(
        stream_file(account, drive_file_id),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{drive_file_id}"'},
    )


@router.get("/shared/{account_index}/{folder_id}/children")
async def list_shared_children(account_index: int, folder_id: str, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM drive_accounts WHERE account_index = ?", [account_index])
    if not rows:
        raise HTTPException(status_code=503, detail="Account not connected")
    account = DriveAccount.from_row(rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        return list_shared_folder_children(account, folder_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shared/{account_index}/{drive_file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shared_file(account_index: int, drive_file_id: str, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM drive_accounts WHERE account_index = ?", [account_index])
    if not rows:
        raise HTTPException(status_code=503, detail="Account not connected")
    account = DriveAccount.from_row(rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        remove_shared_file(account, drive_file_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shared")
async def list_shared(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    acc_rows = await d1.execute("SELECT * FROM drive_accounts WHERE is_connected = 1")
    accounts = [DriveAccount.from_row(r) for r in acc_rows]
    results = []
    for account in accounts:
        try:
            results.extend(list_shared_files(account))
        except Exception:
            pass
    return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)


@router.get("/trash")
async def list_trash(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    acc_rows = await d1.execute("SELECT * FROM drive_accounts WHERE is_connected = 1")
    accounts = [DriveAccount.from_row(r) for r in acc_rows]
    results = []
    for account in accounts:
        try:
            results.extend(list_trash_files(account))
        except Exception:
            pass
    return sorted(results, key=lambda x: x.get("trashed_at", ""), reverse=True)


@router.post("/trash/{account_index}/{drive_file_id}/restore", status_code=status.HTTP_204_NO_CONTENT)
async def restore_trash_file(account_index: int, drive_file_id: str, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM drive_accounts WHERE account_index = ?", [account_index])
    if not rows:
        raise HTTPException(status_code=503, detail="Account not connected")
    account = DriveAccount.from_row(rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        restore_file(account, drive_file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/trash/{account_index}/{drive_file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trash_file(account_index: int, drive_file_id: str, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM drive_accounts WHERE account_index = ?", [account_index])
    if not rows:
        raise HTTPException(status_code=503, detail="Account not connected")
    account = DriveAccount.from_row(rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")
    try:
        delete_drive_file(account, drive_file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
