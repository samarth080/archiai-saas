import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings

ALGORITHM = "HS256"

# Short-lived access token (Phase 0 C2) — was 7 days, which meant a leaked token
# was a week-long takeover with no way to revoke it. Refresh tokens (below) carry
# the long-lived session and are revocable.
ACCESS_TOKEN_EXPIRE_MINUTES = 45
REFRESH_TOKEN_EXPIRE_DAYS = 30

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def _create_token(user_id: str, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    jti = str(uuid.uuid4())
    payload = {
        "sub": user_id,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, jti, expire


def create_access_token(user_id: str) -> str:
    token, _, _ = _create_token(
        user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return token


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Return (token, expires_at). The caller persists a hash of the token so it
    can be revoked before it naturally expires."""
    token, _, expire = _create_token(
        user_id, TOKEN_TYPE_REFRESH, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return token, expire


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Decode and validate a JWT. Raises ValueError on any invalid/expired token
    or on a token whose `type` claim does not match `expected_type` — this is
    what stops a refresh token being replayed on an access-protected route."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    if payload.get("sub") is None:
        raise ValueError("Invalid token payload")
    if expected_type is not None and payload.get("type") != expected_type:
        raise ValueError("Wrong token type")
    return payload


def decode_access_token(token: str) -> str:
    payload = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    return payload["sub"]
