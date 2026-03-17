import io
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import get_d1
from models.models import DriveAccount, Profile
from services.auth_service import verify_token
from services.d1_client import D1Client
from services.drive_service import download_file, get_or_create_profile_folder, upload_file

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None


async def _get_or_create_profile(d1: D1Client) -> Profile:
    rows = await d1.execute("SELECT * FROM profile LIMIT 1")
    if rows:
        return Profile.from_row(rows[0])
    await d1.execute("INSERT INTO profile (display_name, bio) VALUES (NULL, NULL)")
    rows = await d1.execute("SELECT * FROM profile LIMIT 1")
    return Profile.from_row(rows[0])


@router.get("")
async def get_profile(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    profile = await _get_or_create_profile(d1)
    return {
        "display_name": profile.display_name,
        "bio": profile.bio,
        "has_avatar": profile.avatar_drive_file_id is not None,
    }


@router.put("")
async def update_profile(body: ProfileUpdate, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    profile = await _get_or_create_profile(d1)
    parts, params = [], []
    if body.display_name is not None:
        parts.append("display_name = ?")
        params.append(body.display_name)
    if body.bio is not None:
        parts.append("bio = ?")
        params.append(body.bio)
    if parts:
        params.append(profile.id)
        await d1.execute(f"UPDATE profile SET {', '.join(parts)} WHERE id = ?", params)
    return {"ok": True}


@router.post("/avatar", status_code=status.HTTP_200_OK)
async def upload_avatar(file: UploadFile, d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    acc_rows = await d1.execute("SELECT * FROM drive_accounts WHERE is_connected = 1 LIMIT 1")
    if not acc_rows:
        raise HTTPException(status_code=503, detail="No connected accounts")
    account = DriveAccount.from_row(acc_rows[0])

    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "image/jpeg"
    content = await file.read()

    folder_id = get_or_create_profile_folder(account)
    result = upload_file(account, io.BytesIO(content), "_gdriveGenie_avatar_", mime_type, parent_folder_id=folder_id)

    profile = await _get_or_create_profile(d1)
    await d1.execute(
        "UPDATE profile SET avatar_drive_file_id = ?, avatar_account_index = ? WHERE id = ?",
        [result["drive_file_id"], account.account_index, profile.id],
    )
    return {"ok": True}


@router.get("/avatar")
async def get_avatar(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    rows = await d1.execute("SELECT * FROM profile LIMIT 1")
    if not rows:
        raise HTTPException(status_code=404, detail="No avatar set")
    profile = Profile.from_row(rows[0])
    if not profile.avatar_drive_file_id:
        raise HTTPException(status_code=404, detail="No avatar set")

    acc_rows = await d1.execute(
        "SELECT * FROM drive_accounts WHERE account_index = ?", [profile.avatar_account_index]
    )
    if not acc_rows:
        raise HTTPException(status_code=503, detail="Account not available")
    account = DriveAccount.from_row(acc_rows[0])
    if not account.is_connected:
        raise HTTPException(status_code=503, detail="Account not available")

    content = download_file(account, profile.avatar_drive_file_id)
    return StreamingResponse(io.BytesIO(content), media_type="image/jpeg")
