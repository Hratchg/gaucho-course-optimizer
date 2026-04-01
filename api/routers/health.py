from fastapi import APIRouter
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> dict:
    """Health check — returns immediately with no database query.

    Used by UptimeRobot to keep Render service warm (API-05).
    Must NOT have Depends(get_db) — health check must succeed even during DB downtime.
    """
    return {"status": "ok"}
