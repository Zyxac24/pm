import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


class AuthError(Exception):
    pass


def _get_secret_key() -> str:
    key = os.getenv("JWT_SECRET_KEY", "kanban-dev-secret-change-in-production")
    return key


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired.")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token.")
