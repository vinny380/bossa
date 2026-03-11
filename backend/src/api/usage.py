"""Usage endpoint."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.dependencies import get_workspace_id_with_tracking
from src.usage import LIMITS, get_account_id, get_tier, get_usage

router = APIRouter(tags=["usage"])


class UsageResponse(BaseModel):
    storage_mb: float
    files_count: int
    requests_today: int
    tier: str
    limits: dict


@router.get("/usage", response_model=UsageResponse)
async def get_usage_endpoint(
    workspace_id: str = Depends(get_workspace_id_with_tracking),
) -> UsageResponse:
    """Return current usage and limits for the account."""
    account_id = await get_account_id(workspace_id)
    if account_id is None:
        return UsageResponse(
            storage_mb=0,
            files_count=0,
            requests_today=0,
            tier="free",
            limits=LIMITS["free"],
        )
    tier = await get_tier(account_id)
    usage = await get_usage(account_id)
    return UsageResponse(
        storage_mb=round(usage["storage_mb"], 2),
        files_count=usage["files_count"],
        requests_today=usage["requests_today"],
        tier=tier,
        limits=LIMITS[tier],
    )
