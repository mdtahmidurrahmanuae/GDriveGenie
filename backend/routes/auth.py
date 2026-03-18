import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from googleapiclient.discovery import build as gbuild
from pydantic import BaseModel

import config
from database import PBClient, get_pb
from services.auth_service import (
    create_access_token,
    encrypt_token,
    verify_token,
)
from services.drive_service import get_oauth_flow, sync_files_from_drives

router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory store for PKCE verifiers: (user_id, account_index) → verifier
_pending_verifiers: dict[str, str] = {}


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(body: LoginRequest, response: Response, pb: PBClient = Depends(get_pb)):
    try:
        data = await pb.auth_user(body.email, body.password)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    record = data.get("record", {})
    token = create_access_token(
        user_id=record["id"],
        email=record.get("email", ""),
        is_super_admin=bool(record.get("is_super_admin", False)),
        storage_limit_bytes=int(record.get("storage_limit_bytes") or 16106127360),
    )
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
    )
    return {
        "ok": True,
        "user": {
            "id": record["id"],
            "email": record.get("email"),
            "display_name": record.get("display_name"),
            "is_super_admin": record.get("is_super_admin", False),
            "storage_limit_bytes": record.get("storage_limit_bytes"),
            "storage_used_bytes": record.get("storage_used_bytes"),
        },
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me")
async def me(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    try:
        record = await pb.get_record("gdrive_users", user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": record["id"],
        "email": record.get("email"),
        "display_name": record.get("display_name"),
        "is_super_admin": record.get("is_super_admin", False),
        "storage_limit_bytes": record.get("storage_limit_bytes"),
        "storage_used_bytes": record.get("storage_used_bytes"),
    }


@router.get("/oauth/new")
async def get_new_oauth_url(
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]

    # Remove orphaned disconnected accounts for this user
    orphans = await pb.list_records(
        "gdrive_accounts",
        filter=f'user="{user_id}" && is_connected=false && email=""',
    )
    for o in orphans:
        try:
            await pb.delete_record("gdrive_accounts", o["id"])
        except Exception:
            pass

    # Find next account_index for this user
    existing = await pb.list_records(
        "gdrive_accounts", filter=f'user="{user_id}"', sort="-account_index", per_page=1
    )
    max_idx = int(existing[0]["account_index"]) if existing else 0
    new_index = max_idx + 1

    new_acc = await pb.create_record("gdrive_accounts", {
        "user": user_id,
        "account_index": new_index,
        "is_connected": False,
    })
    acc_id = new_acc["id"]

    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    # state encodes user_id and account PB id
    state_key = f"{user_id}:{acc_id}"
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
        state=state_key,
    )
    if flow.code_verifier:
        _pending_verifiers[state_key] = flow.code_verifier
    return {"auth_url": auth_url}


@router.get("/oauth/{account_id}/reconnect")
async def get_oauth_url_reconnect(
    account_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc = await pb.get_record("gdrive_accounts", account_id)
    if acc.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Not your account")

    state_key = f"{user_id}:{account_id}"
    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
        state=state_key,
    )
    if flow.code_verifier:
        _pending_verifiers[state_key] = flow.code_verifier
    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    background_tasks: BackgroundTasks,
    pb: PBClient = Depends(get_pb),
):
    try:
        user_id, acc_id = state.split(":", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    code_verifier = _pending_verifiers.pop(state, None)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    creds = flow.credentials

    service = gbuild("drive", "v3", credentials=creds)
    about = service.about().get(fields="user").execute()
    email = about.get("user", {}).get("emailAddress", "")

    await pb.update_record("gdrive_accounts", acc_id, {
        "email": email,
        "refresh_token_encrypted": encrypt_token(creds.refresh_token),
        "is_connected": True,
    })

    async def _sync_bg():
        from services.pb_client import PBClient as _PB
        bg_pb = _PB()
        try:
            await sync_files_from_drives(bg_pb, user_id)
        finally:
            await bg_pb.aclose()

    background_tasks.add_task(asyncio.run, _sync_bg())

    return Response(
        status_code=302,
        headers={"Location": f"{config.FRONTEND_URL}/dashboard/settings"},
    )
