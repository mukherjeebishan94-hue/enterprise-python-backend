from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

pwd_context = PasswordHash((BcryptHasher(),))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a raw password against its hashed version."""
    try:
        truncated = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(truncated, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hashes a plain text password."""
    truncated = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated)


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Generates a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)