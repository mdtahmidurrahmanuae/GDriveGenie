"""Super-admin only routes: user management, storage limits."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from database import PBClient, get_pb
from models.models import GDUser
from services.auth_service import require_super_admin, verify_token

router = APIRouter(prefix="/admin", tags=["admin"])

_15_GB = 16106127360


class CreateUser(BaseModel):
    email: str
    password: str
    display_name: str = ""
    storage_limit_bytes: int = _15_GB
    is_super_admin: bool = False


class UpdateStorage(BaseModel):
    storage_limit_bytes: int


class UpdateUser(BaseModel):
    display_name: str | None = None
    storage_limit_bytes: int | None = None
    is_super_admin: bool | None = None


def _super_admin(token: dict = Depends(verify_token)) -> dict:
    return require_super_admin(token)


@router.get("/users")
async def list_users(
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    rows = await pb.list_records("gdrive_users", sort="email", per_page=500)
    return [_user_to_dict(GDUser.from_pb(r)) for r in rows]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUser,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    if body.storage_limit_bytes < 0:
        raise HTTPException(status_code=400, detail="Storage limit must be >= 0")
    try:
        row = await pb.create_record("gdrive_users", {
            "email": body.email,
            "password": body.password,
            "passwordConfirm": body.password,
            "display_name": body.display_name,
            "is_super_admin": body.is_super_admin,
            "storage_limit_bytes": body.storage_limit_bytes,
            "storage_used_bytes": 0,
            "emailVisibility": True,
            "verified": True,
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _user_to_dict(GDUser.from_pb(row))


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    row = await pb.get_record("gdrive_users", user_id)
    return _user_to_dict(GDUser.from_pb(row))


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUser,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    updates: dict = {}
    if body.display_name is not None:
        updates["display_name"] = body.display_name
    if body.storage_limit_bytes is not None:
        if body.storage_limit_bytes < 0:
            raise HTTPException(status_code=400, detail="Storage limit must be >= 0")
        updates["storage_limit_bytes"] = body.storage_limit_bytes
    if body.is_super_admin is not None:
        updates["is_super_admin"] = body.is_super_admin
    if updates:
        row = await pb.update_record("gdrive_users", user_id, updates)
        return _user_to_dict(GDUser.from_pb(row))
    return {"ok": True}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    current = token["sub"]
    if user_id == current:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await pb.delete_record("gdrive_users", user_id)


@router.get("/stats")
async def admin_stats(
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(_super_admin),
):
    total_users = await pb.count_records("gdrive_users")
    total_files = await pb.count_records("gdrive_files")
    total_accounts = await pb.count_records("gdrive_accounts", filter="is_connected=true")
    users = await pb.list_records("gdrive_users", per_page=2000)
    total_used = sum(int(u.get("storage_used_bytes") or 0) for u in users)
    total_limit = sum(int(u.get("storage_limit_bytes") or _15_GB) for u in users)
    return {
        "total_users": total_users,
        "total_files": total_files,
        "connected_accounts": total_accounts,
        "total_storage_used_bytes": total_used,
        "total_storage_limit_bytes": total_limit,
    }


def _user_to_dict(u: GDUser) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "display_name": u.display_name,
        "is_super_admin": u.is_super_admin,
        "storage_limit_bytes": u.storage_limit_bytes,
        "storage_used_bytes": u.storage_used_bytes,
    }
