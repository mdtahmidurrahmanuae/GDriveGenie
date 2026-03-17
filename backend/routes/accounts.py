from fastapi import APIRouter, Depends

from database import get_d1
from models.models import DriveAccount
from services.auth_service import verify_token
from services.d1_client import D1Client
from services.drive_service import get_all_quotas

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(d1: D1Client = Depends(get_d1), _=Depends(verify_token)):
    quotas = await get_all_quotas(d1)
    connected_indices = {q["account_index"] for q in quotas}

    rows = await d1.execute("SELECT * FROM drive_accounts WHERE is_connected = 0")
    disconnected = [DriveAccount.from_row(r) for r in rows]

    for acc in disconnected:
        if acc.account_index not in connected_indices:
            quotas.append({
                "account_index": acc.account_index,
                "email": acc.email,
                "is_connected": False,
                "used": 0,
                "limit": 0,
                "free": 0,
            })

    return sorted(quotas, key=lambda x: x["account_index"])


@router.delete("/{account_index}")
async def disconnect_account(
    account_index: int,
    d1: D1Client = Depends(get_d1),
    _=Depends(verify_token),
):
    await d1.execute("DELETE FROM files WHERE account_index = ?", [account_index])
    await d1.execute(
        "UPDATE drive_accounts SET is_connected = 0, refresh_token = NULL, "
        "access_token = NULL, token_expiry = NULL WHERE account_index = ?",
        [account_index],
    )
    return {"ok": True}
