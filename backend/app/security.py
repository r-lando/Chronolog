"""
Security primitives: password hashing and JWT handling.

Design decisions worth noting:
- Passwords are hashed with bcrypt (via passlib), never stored or logged
  in plaintext. bcrypt includes a per-password salt automatically.
- JWTs are short-lived (see ACCESS_TOKEN_EXPIRE_MINUTES) and signed with
  HS256 using a secret loaded from the environment, never hardcoded.
- The token payload carries only the user id ("sub") and an expiry —
  no email, role, or other data that would go stale or leak on decode.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> UUID | None:
    """Returns the user id encoded in the token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None
    except (JWTError, ValueError):
        return None
