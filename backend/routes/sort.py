import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from database import PBClient, get_pb
from services.auth_service import verify_token
from services.sort_service import sort_all_drives

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sort", tags=["sort"])


@router.post("")
async def sort_files(
    background_tasks: BackgroundTasks,
    pb: PBClient = Depends(get_pb),
    token: dict = Depends(verify_token),
):
    """
    Trigger a full MIME-type sort across all connected drives for the current user.
    The sort runs synchronously and returns per-account stats.
    """
    user_id = token["sub"]
    try:
        results = await sort_all_drives(pb, user_id)
    except Exception as e:
        logger.exception("sort_all_drives failed for user %s", user_id)
        raise HTTPException(status_code=500, detail=str(e))

    total_moved = sum(r.get("moved", 0) for r in results)
    total_skipped = sum(r.get("skipped", 0) for r in results)
    total_errors = sum(r.get("errors", 0) for r in results)

    return {
        "ok": True,
        "total_moved": total_moved,
        "total_skipped": total_skipped,
        "total_errors": total_errors,
        "accounts": results,
    }
