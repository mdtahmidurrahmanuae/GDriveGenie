import io
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import PBClient, get_pb
from models.models import DriveAccount, GDUser
from services.auth_service import verify_token
from services.drive_service import download_file, get_or_create_profile_folder, upload_file

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None


@router.get("")
async def get_profile(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    record = await pb.get_record("gdrive_users", user_id)
    user = GDUser.from_pb(record)
    return {
        "display_name": user.display_name,
        "bio": user.bio,
        "has_avatar": bool(user.avatar_drive_file_id),
        "storage_limit_bytes": user.storage_limit_bytes,
        "storage_used_bytes": user.storage_used_bytes,
    }


@router.put("")
async def update_profile(
    body: ProfileUpdate,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    updates: dict = {}
    if body.display_name is not None:
        updates["display_name"] = body.display_name
    if body.bio is not None:
        updates["bio"] = body.bio
    if updates:
        await pb.update_record("gdrive_users", user_id, updates)
    return {"ok": True}


@router.post("/avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(
    file: UploadFile,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc_rows = await pb.list_records(
        "gdrive_accounts",
        filter=f'user="{user_id}" && is_connected=true',
        per_page=1,
    )
    if not acc_rows:
        raise HTTPException(status_code=503, detail="No connected accounts")
    account = DriveAccount.from_pb(acc_rows[0])

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "image/jpeg"
    content = await file.read()

    folder_id = get_or_create_profile_folder(account)
    result = upload_file(account, io.BytesIO(content), "_gdriveGenie_avatar_", mime_type, parent_folder_id=folder_id)

    await pb.update_record("gdrive_users", user_id, {
        "avatar_drive_file_id": result["drive_file_id"],
        "avatar_account_id": acc_rows[0]["id"],
    })
    return {"ok": True}


@router.get("/avatar")
async def get_avatar(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    record = await pb.get_record("gdrive_users", user_id)
    user = GDUser.from_pb(record)
    if not user.avatar_drive_file_id:
        raise HTTPException(status_code=404, detail="No avatar set")

    acc_row = await pb.get_record("gdrive_accounts", user.avatar_account_id)
    account = DriveAccount.from_pb(acc_row)
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not available")

    content = download_file(account, user.avatar_drive_file_id)
    return StreamingResponse(io.BytesIO(content), media_type="image/jpeg")
