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
- A small middleware adds defense-in-depth security headers to every
  response (see add_security_headers below).
- Interactive API docs (/docs, /redoc) are only served when
  ENVIRONMENT is not "production" — useful during development, but a
  full schema of every endpoint isn't something a production deployment
  should hand out to anyone who asks for it.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import auth, ctf, evidence, labs, mitre, public, reports, roadmap, search, skills, stats, tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tala")

settings = get_settings()
_is_production = settings.environment == "production"

app = FastAPI(
    title="TALA — Cybersecurity Lab Journal API",
    version="0.1.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Defense-in-depth headers that cost nothing and help regardless of
    what else is in place:
    - X-Content-Type-Options stops a browser from guessing a response's
      type differently than the Content-Type we actually sent (relevant
      mainly for evidence file downloads).
    - X-Frame-Options blocks this app from being embedded in a hidden
      iframe on someone else's page (clickjacking).
    - Referrer-Policy avoids leaking full URLs (which can contain
      portfolio slugs or other path details) to third-party sites a
      user navigates to afterward.
    - Strict-Transport-Security only makes sense once the app is
      actually served over HTTPS, so it's gated on cookie_secure, which
      is the same flag that governs whether the auth cookie itself
      requires HTTPS.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.cookie_secure:
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


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
app.include_router(skills.router, prefix="/api/v1")
app.include_router(tools.router, prefix="/api/v1")
app.include_router(mitre.router, prefix="/api/v1")
app.include_router(ctf.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(roadmap.router, prefix="/api/v1")
app.include_router(public.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
