"""
Shared FastAPI dependencies.

get_current_user() is the single choke point every protected route goes
through. It reads the JWT from an HttpOnly cookie (never from a header
or query string, which are easier to leak via logs/history/XSS), and
raises 401 if the token is missing, invalid, expired, or the user no
longer exists/is inactive.
"""

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import decode_access_token

COOKIE_NAME = "tala_access_token"


def get_current_user(
    tala_access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )

    if not tala_access_token:
        raise credentials_error

    user_id = decode_access_token(tala_access_token)
    if user_id is None:
        raise credentials_error

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error

    return user
