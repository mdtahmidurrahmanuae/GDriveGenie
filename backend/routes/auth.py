import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from googleapiclient.discovery import build as gbuild
from pydantic import BaseModel

import config
from database import get_d1
from services.auth_service import (
    create_access_token,
    encrypt_token,
    verify_pin,
    verify_token,
)
from services.d1_client import D1Client
from services.drive_service import get_oauth_flow, sync_files_from_drives

router = APIRouter(prefix="/auth", tags=["auth"])

_pending_verifiers: dict[int, str] = {}


class LoginRequest(BaseModel):
    pin: str


@router.post("/login")
def login(body: LoginRequest, response: Response):
    if not verify_pin(body.pin):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PIN")
    token = create_access_token({"sub": "dashboard"})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/oauth/new")
async def get_new_oauth_url(
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    # Remove orphaned email-less disconnected placeholders from previous attempts
    await d1.execute(
        "DELETE FROM drive_accounts WHERE is_connected = 0 AND email IS NULL AND refresh_token IS NULL"
    )

    rows = await d1.execute("SELECT MAX(account_index) AS max_idx FROM drive_accounts")
    max_idx = rows[0]["max_idx"] if rows and rows[0]["max_idx"] is not None else 0
    new_index = max_idx + 1

    await d1.execute(
        "INSERT INTO drive_accounts (account_index, is_connected) VALUES (?, 0)",
        [new_index],
    )

    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
        state=str(new_index),
    )
    if flow.code_verifier:
        _pending_verifiers[new_index] = flow.code_verifier
    return {"auth_url": auth_url}


@router.get("/oauth/{account_index}")
def get_oauth_url(account_index: int, _=Depends(verify_token)):
    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
        state=str(account_index),
    )
    if flow.code_verifier:
        _pending_verifiers[account_index] = flow.code_verifier
    return {"auth_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    request: Request,
    background_tasks: BackgroundTasks,
    d1: D1Client = Depends(get_d1),
):
    account_index = int(state)
    redirect_uri = config.BACKEND_URL.rstrip("/") + "/api/auth/callback"
    flow = get_oauth_flow(redirect_uri)
    code_verifier = _pending_verifiers.pop(account_index, None)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    creds = flow.credentials

    service = gbuild("drive", "v3", credentials=creds)
    about = service.about().get(fields="user").execute()
    email = about.get("user", {}).get("emailAddress", "")

    rows = await d1.execute(
        "SELECT id FROM drive_accounts WHERE account_index = ?", [account_index]
    )
    if rows:
        await d1.execute(
            "UPDATE drive_accounts SET email = ?, refresh_token = ?, is_connected = 1 WHERE account_index = ?",
            [email, encrypt_token(creds.refresh_token), account_index],
        )
    else:
        await d1.execute(
            "INSERT INTO drive_accounts (account_index, email, refresh_token, is_connected) VALUES (?, ?, ?, 1)",
            [account_index, email, encrypt_token(creds.refresh_token)],
        )

    async def _sync_bg() -> None:
        from services.d1_client import D1Client as _D1Client
        bg_d1 = _D1Client()
        try:
            await sync_files_from_drives(bg_d1)
        finally:
            await bg_d1.aclose()

    background_tasks.add_task(asyncio.run, _sync_bg())

    return Response(
        status_code=302,
        headers={"Location": f"{config.FRONTEND_URL}/dashboard/settings"},
    )
