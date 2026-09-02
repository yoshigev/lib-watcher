from typing import Optional
from fastapi import APIRouter, Header, Query, HTTPException, status
from app.config import settings
from app.scheduler import check_all_watched_books

router = APIRouter(prefix="/api/cron", tags=["cron"])

@router.get("/check")
@router.post("/check")
def trigger_availability_check(
    secret: Optional[str] = Query(None),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret")
):
    """
    Protected endpoint to trigger periodic book availability checks.
    Can be invoked by GitHub Actions, cron-job.org, or external cron.
    """
    provided_secret = secret or x_cron_secret
    if not provided_secret or provided_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing cron secret token."
        )

    result = check_all_watched_books()
    return result
