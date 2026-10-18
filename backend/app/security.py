"""Password and signed access-token primitives. No role claims grant authority."""
from datetime import datetime, timedelta, timezone
import secrets
import uuid
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from app.config import Settings

# Argon2id: 64 MiB, 3 iterations, 4 lanes (RFC 9106 low-memory profile).
password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str | None) -> bool:
    try:
        valid = password_hasher.verify(stored_hash or _dummy_hash, password)
        return valid and stored_hash is not None
    except (VerificationError, InvalidHashError):
        return False


def issue_token(user_id: str, settings: Settings, session_id: str | None = None) -> str:
    if settings.jwt_secret is None:
        raise RuntimeError("Authentication is not configured")
    now = datetime.now(timezone.utc)
    return jwt.encode({"sub": user_id, "iat": now, "nbf": now,
                       "exp": now + timedelta(minutes=settings.access_token_minutes),
                       "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
                       "jti": session_id or str(uuid.uuid4())},
                      settings.jwt_secret.get_secret_value(), algorithm="HS256")


def decode_token(token: str, settings: Settings) -> str:
    if settings.jwt_secret is None:
        raise jwt.InvalidTokenError()
    payload = jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"],
        issuer=settings.jwt_issuer, audience=settings.jwt_audience,
        options={"require": ["sub", "iat", "nbf", "exp", "iss", "aud", "jti"]})
    try:
        return str(uuid.UUID(payload["sub"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise jwt.InvalidTokenError() from exc


def token_session_id(token: str, settings: Settings) -> str:
    decode_token(token, settings)
    return jwt.decode(token,settings.jwt_secret.get_secret_value(),algorithms=['HS256'],issuer=settings.jwt_issuer,audience=settings.jwt_audience)['jti']
