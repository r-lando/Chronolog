"""
TALA API entrypoint.

Security-relevant wiring done here:
- CORS is restricted to explicit origins from settings, with credentials
  allowed (required so the HttpOnly auth cookie is sent cross-origin
  from the Vite dev server to the API during local development).
- A global exception handler catches any unhandled server error, logs
  the real details server-side, and returns a generic message to the
  client — so stack traces, file paths, and internal details never leak
  to a user or attacker.
- The slowapi rate limiter is attached at the app level so per-route
  @limiter.limit(...) decorators (see routers/auth.py) work.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import auth, evidence, labs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tala")

settings = get_settings()

app = FastAPI(title="TALA — Cybersecurity Lab Journal API", version="0.1.0")

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please slow down and try again shortly."},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    # Full details go to the server log only — never to the client.
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )


@app.get("/api/v1/health", tags=["health"])
def health_check():
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(labs.router, prefix="/api/v1")
app.include_router(evidence.router, prefix="/api/v1")
