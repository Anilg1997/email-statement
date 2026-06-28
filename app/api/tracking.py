from fastapi import APIRouter, Query
from typing import Optional
from app.services.access_tracker import tracker

router = APIRouter(tags=["tracking"])


@router.get("/access-log")
async def get_access_log(accountId: Optional[str] = Query(None)):
    """Get access logs, optionally filtered by account ID."""
    logs = tracker.get_logs(accountId)
    stats = tracker.get_stats()
    return {"logs": logs, "stats": stats}
