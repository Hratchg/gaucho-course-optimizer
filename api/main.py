import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from api.rate_limit import limiter
from api.routers import health, courses, professors, quarters
from api.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gaucho Course Optimizer API",
    description="REST API exposing UCSB professor rankings by Gaucho Score",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


async def catch_unhandled_errors(request: Request, call_next):
    """Convert unhandled exceptions into a JSON 500 *inside* the CORS middleware.

    Starlette's built-in ServerErrorMiddleware sits outside every user
    middleware, so an exception escaping a route produces a bare
    "Internal Server Error" with no Access-Control-Allow-Origin header. The
    browser then reports an opaque "Failed to fetch" and the SPA cannot tell a
    server fault from an offline client. Handling the exception here — inside
    CORSMiddleware — lets the response travel back out through CORS and pick
    up the header, so the frontend sees a real 500.

    The correlation id is returned to the client and logged alongside the
    traceback so a user-reported error can be found in the Render logs.
    """
    try:
        return await call_next(request)
    except Exception:
        error_id = uuid.uuid4().hex[:12]
        logger.exception(
            "Unhandled error %s on %s %s", error_id, request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error_id": error_id,
            },
        )


# Order matters: Starlette applies the most recently added middleware
# outermost, so CORS must be registered last to wrap the error handler.
app.add_middleware(BaseHTTPMiddleware, dispatch=catch_unhandled_errors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins(),
    allow_methods=["GET"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "Retry-After"],
)


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and request.url.path.startswith("/courses"):
        response.headers.setdefault("Cache-Control", "public, max-age=60")
    return response

app.include_router(health.router)
app.include_router(courses.router, prefix="/courses", tags=["courses"])
app.include_router(professors.router, prefix="/professors", tags=["professors"])
app.include_router(quarters.router, prefix="/quarters", tags=["quarters"])
