"""
Folder sharing:
  - share_type = "user"     → shared with a specific GDriveGenie user by email
  - share_type = "public"   → anyone with the link can view
  - share_type = "password" → anyone with the link + password can view

Public/password share links are served at:
  GET /api/shares/view/{token}         → list folder contents
  GET /api/shares/view/{token}/{file_id}/download  → download file
"""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from database import PBClient, get_pb
from models.models import Folder, Share
from services.auth_service import hash_share_password, verify_share_password, verify_token

router = APIRouter(prefix="/shares", tags=["shares"])


class ShareCreate(BaseModel):
    folder_id: str
    share_type: str           # "user" | "public" | "password"
    shared_with_email: str | None = None   # for share_type="user"
    password: str | None = None            # for share_type="password"
    expires_at: str | None = None          # ISO datetime string, optional


class SharePasswordCheck(BaseModel):
    password: str


# ---------------------------------------------------------------------------
# CRUD (authenticated user)
# ---------------------------------------------------------------------------

@router.get("/folder/{folder_id}")
async def list_folder_shares(
    folder_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    folder = await pb.get_record("gdrive_folders", folder_id)
    if folder.get("user") != user_id:
        raise HTTPException(status_code=403)
    rows = await pb.list_records("gdrive_shares", filter=f'folder="{folder_id}"')
    return [_share_to_dict(Share.from_pb(r)) for r in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_share(
    body: ShareCreate,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]

    if body.share_type not in ("user", "public", "password"):
        raise HTTPException(status_code=400, detail="Invalid share_type")

    folder = await pb.get_record("gdrive_folders", body.folder_id)
    if folder.get("user") != user_id:
        raise HTTPException(status_code=403)

    data: dict = {
        "folder": body.folder_id,
        "created_by": user_id,
        "share_type": body.share_type,
        "token": secrets.token_urlsafe(24),
    }

    if body.share_type == "user":
        if not body.shared_with_email:
            raise HTTPException(status_code=400, detail="shared_with_email required")
        # Look up target user
        targets = await pb.list_records(
            "gdrive_users", filter=f'email="{body.shared_with_email}"', per_page=1
        )
        if not targets:
            raise HTTPException(status_code=404, detail="User not found")
        data["shared_with"] = targets[0]["id"]

    if body.share_type == "password":
        if not body.password:
            raise HTTPException(status_code=400, detail="password required")
        data["password_hash"] = hash_share_password(body.password)

    if body.expires_at:
        data["expires_at"] = body.expires_at

    row = await pb.create_record("gdrive_shares", data)
    return _share_to_dict(Share.from_pb(row))


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share(
    share_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    row = await pb.get_record("gdrive_shares", share_id)
    if row.get("created_by") != user_id:
        raise HTTPException(status_code=403)
    await pb.delete_record("gdrive_shares", share_id)


# ---------------------------------------------------------------------------
# Shared with me
# ---------------------------------------------------------------------------

@router.get("/with-me")
async def shared_with_me(
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    rows = await pb.list_records(
        "gdrive_shares",
        filter=f'shared_with="{user_id}"',
        expand="folder",
    )
    result = []
    for row in rows:
        share = Share.from_pb(row)
        folder_data = row.get("expand", {}).get("folder") or {}
        result.append({
            **_share_to_dict(share),
            "folder_name": folder_data.get("name", ""),
        })
    return result


# ---------------------------------------------------------------------------
# Public link access (no auth required)
# ---------------------------------------------------------------------------

@router.get("/view/{token}")
async def view_shared_folder(
    token: str,
    pb: PBClient = Depends(get_pb),
):
    share = await _resolve_share(pb, token, password=None, check_password=False)
    if share.share_type == "password":
        # Password shares require verification first
        return {"requires_password": True, "share_id": share.id}

    return await _get_folder_contents(pb, share)


@router.post("/view/{token}/unlock")
async def unlock_share(
    token: str,
    body: SharePasswordCheck,
    pb: PBClient = Depends(get_pb),
):
    share = await _resolve_share(pb, token, password=body.password, check_password=True)
    return await _get_folder_contents(pb, share)


@router.get("/view/{token}/{file_id}/download")
async def download_shared_file(
    token: str,
    file_id: str,
    pb: PBClient = Depends(get_pb),
):
    share = await _resolve_share(pb, token, password=None, check_password=False)
    if share.share_type == "password":
        raise HTTPException(status_code=403, detail="Password required. Use /unlock first.")

    # Verify file belongs to the shared folder
    mappings = await pb.list_records(
        "gdrive_folder_files",
        filter=f'folder="{share.folder_id}" && file="{file_id}"',
        per_page=1,
    )
    if not mappings:
        raise HTTPException(status_code=404, detail="File not in this shared folder")

    from fastapi.responses import StreamingResponse
    from models.models import DriveAccount
    from services.drive_service import stream_file

    file_rec = await pb.get_record("gdrive_files", file_id)
    acc_rec = await pb.get_record("gdrive_accounts", file_rec.get("account", ""))
    account = DriveAccount.from_pb(acc_rec)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not connected")

    return StreamingResponse(
        stream_file(account, file_rec["drive_file_id"]),
        media_type=file_rec.get("mime_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_rec.get("file_name", "file")}"'},
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_share(pb: PBClient, token: str, password: str | None, check_password: bool) -> Share:
    rows = await pb.list_records("gdrive_shares", filter=f'token="{token}"', per_page=1)
    if not rows:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    share = Share.from_pb(rows[0])

    # Check expiry
    if share.expires_at:
        try:
            exp = datetime.fromisoformat(share.expires_at.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                raise HTTPException(status_code=410, detail="Share link has expired")
        except ValueError:
            pass

    # Password verification
    if check_password and share.share_type == "password":
        if not password or not share.password_hash:
            raise HTTPException(status_code=403, detail="Password required")
        if not verify_share_password(password, share.password_hash):
            raise HTTPException(status_code=403, detail="Incorrect password")

    return share


async def _get_folder_contents(pb: PBClient, share: Share) -> dict:
    folder_rec = await pb.get_record("gdrive_folders", share.folder_id)
    mappings = await pb.list_records(
        "gdrive_folder_files",
        filter=f'folder="{share.folder_id}"',
        expand="file",
        per_page=2000,
    )
    files = []
    for m in mappings:
        file_rec = m.get("expand", {}).get("file") or {}
        if file_rec:
            files.append({
                "id": file_rec["id"],
                "file_name": file_rec.get("file_name", ""),
                "size": file_rec.get("size", 0),
                "mime_type": file_rec.get("mime_type"),
                "has_thumbnail": bool(file_rec.get("thumbnail_link")),
            })
    return {
        "folder_name": folder_rec.get("name", ""),
        "share_type": share.share_type,
        "files": files,
    }


def _share_to_dict(s: Share) -> dict:
    return {
        "id": s.id,
        "folder_id": s.folder_id,
        "share_type": s.share_type,
        "shared_with": s.shared_with,
        "token": s.token,
        "expires_at": s.expires_at,
        "link": f"/shared/{s.token}",
    }
