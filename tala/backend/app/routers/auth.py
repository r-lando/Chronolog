"""
Authentication endpoints.

Security decisions:
- The JWT is delivered as an HttpOnly, SameSite=Lax cookie, not in the
  JSON body. JavaScript can never read it, which removes an entire class
  of XSS-driven token theft. `Secure` is controlled by COOKIE_SECURE so
  it's only sent over HTTPS in production while still working over
  plain HTTP in local Docker development.
- Login failures return the same generic message whether the email
  doesn't exist or the password is wrong, so the endpoint can't be used
  to enumerate valid accounts.
- Both endpoints are rate-limited (see app.rate_limit) to slow down
  credential-stuffing / brute-force attempts.
- Every login and registration is written to the audit log.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.audit import record_audit_event
from app.config import get_settings
from app.database import get_db
from app.dependencies import COOKIE_NAME, get_current_user
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.user import UserPublic
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

GENERIC_LOGIN_ERROR = "Invalid email or password"


def _set_auth_cookie(response: Response, user_id) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_login)
def register(request: Request, payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if settings.allow_single_user_only:
        existing_any_user = db.query(User).first()
        if existing_any_user is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is closed. TALA is configured for a single user.",
            )

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        # Deliberately vague: don't confirm which emails are registered.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to register with these details")

    user = User(
        email=payload.email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # populate user.id before using it below

    record_audit_event(
        db,
        user_id=user.id,
        action="auth.register",
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)

    _set_auth_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserPublic)
@limiter.limit(settings.rate_limit_login)
def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_LOGIN_ERROR)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=GENERIC_LOGIN_ERROR)

    record_audit_event(
        db,
        user_id=user.id,
        action="auth.login",
        resource_type="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    _set_auth_cookie(response, user.id)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user
