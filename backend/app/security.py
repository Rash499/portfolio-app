import datetime as dt
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(subject: str, secret: str, expires_delta: dt.timedelta, token_type: str) -> str:
    now = dt.datetime.utcnow()
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str) -> str:
    return create_token(
        user_id, settings.jwt_secret,
        dt.timedelta(minutes=settings.access_token_expire_minutes), "access",
    )


def create_refresh_token(user_id: str) -> str:
    return create_token(
        user_id, settings.jwt_refresh_secret,
        dt.timedelta(days=settings.refresh_token_expire_days), "refresh",
    )


def decode_token(token: str, secret: str, expected_type: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload.get("sub")
