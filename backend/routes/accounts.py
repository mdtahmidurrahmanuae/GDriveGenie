from fastapi import APIRouter, Depends, HTTPException

from database import PBClient, get_pb
from models.models import DriveAccount
from services.auth_service import verify_token
from services.drive_service import get_all_quotas

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(pb: PBClient = Depends(get_pb), token: dict = Depends(verify_token)):
    user_id = token["sub"]
    quotas = await get_all_quotas(pb, user_id)
    connected_ids = {q["id"] for q in quotas}

    disconnected_rows = await pb.list_records(
        "gdrive_accounts",
        filter=f'user="{user_id}" && is_connected=false',
    )
    for row in disconnected_rows:
        if row["id"] not in connected_ids:
            quotas.append({
                "id": row["id"],
                "account_index": row.get("account_index", 0),
                "email": row.get("email"),
                "is_connected": False,
                "used": 0, "limit": 0, "free": 0,
            })

    return sorted(quotas, key=lambda x: x["account_index"])


@router.delete("/{account_id}")
async def disconnect_account(
    account_id: str,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    user_id = token["sub"]
    acc = await pb.get_record("gdrive_accounts", account_id)
    if acc.get("user") != user_id:
        raise HTTPException(status_code=403, detail="Not your account")

    # Delete all files belonging to this account
    files = await pb.list_records("gdrive_files", filter=f'account="{account_id}"', per_page=2000)
    for f in files:
        try:
            await pb.delete_record("gdrive_files", f["id"])
        except Exception:
            pass

    await pb.update_record("gdrive_accounts", account_id, {
        "is_connected": False,
        "refresh_token_encrypted": "",
        "access_token": "",
        "token_expiry": "",
    })
    return {"ok": True}
