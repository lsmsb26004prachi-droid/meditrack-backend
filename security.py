import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from pwdlib import PasswordHash

# Placeholder key for the prototype only. A real deployment must set the
# MEDI_TRACK_SECRET_KEY environment variable to a long random value.
SECRET_KEY = os.environ.get(
    "MEDI_TRACK_SECRET_KEY", "dev-only-change-me-this-is-not-secure-32b"
)
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Turn a plain password into a one-way hash (Argon2)."""
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Check a typed password against a stored hash."""
    return _password_hash.verify(password, hashed)


def create_access_token(user_id: int, role: str) -> str:
    """Create a signed login token that expires after an hour."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Return the token's contents, or None if it is invalid or expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None