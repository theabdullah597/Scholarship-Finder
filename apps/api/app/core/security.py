import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt

from app.config import settings

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(
    subject: str,
    role: str,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a short-lived (default 15 minutes) JWT access token."""
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "email": email,
        "iat": now,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def generate_secure_token() -> str:
    """Generate a high-entropy cryptographically secure random token string."""
    return secrets.token_urlsafe(48)


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 hash of a raw token for safe persistence."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
