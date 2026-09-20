from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
def health_check() -> dict:
    """Liveness check — returns immediately with no database query.

    Used by UptimeRobot to keep Render service warm (API-05).
    Must NOT have Depends(get_db) — health check must succeed even during DB downtime.
    For a check that verifies the database, use /ready instead.
    """
    return {"status": "ok"}


@router.api_route("/ready", methods=["GET", "HEAD"], response_model=HealthResponse)
def readiness_check(response: Response, db: Session = Depends(get_db)) -> dict:
    """Readiness check — verifies the database is reachable with SELECT 1.

    Returns 200 {"status": "ok"} when the database responds, and
    503 {"status": "unavailable"} when it does not (e.g. Neon quota
    exceeded, suspended branch, bad credentials). Point external
    monitoring (UptimeRobot) at this endpoint so database outages
    actually page someone — /health stays green during DB downtime
    by design.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        response.status_code = 503
        return {"status": "unavailable"}
    return {"status": "ok"}
