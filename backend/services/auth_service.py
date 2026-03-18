from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from cryptography.fernet import Fernet
from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

import config


# ---------------------------------------------------------------------------
# Token encryption (for Google OAuth refresh tokens)
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    return Fernet(config.ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(token: str) -> str:
    return _get_fernet().decrypt(token.encode()).decode()


# ---------------------------------------------------------------------------
# Share-link password hashing
# ---------------------------------------------------------------------------

def hash_share_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_share_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------------------------
# App JWT  (wraps PocketBase user record info)
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, email: str, is_super_admin: bool,
                        storage_limit_bytes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRE_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "is_super_admin": is_super_admin,
        "storage_limit_bytes": storage_limit_bytes,
        "exp": expire,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(access_token: Optional[str] = Cookie(default=None)) -> dict:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(access_token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        if not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def require_super_admin(token: dict) -> dict:
    if not token.get("is_super_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Super-admin access required")
    return token
