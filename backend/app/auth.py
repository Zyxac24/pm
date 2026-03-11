import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

ALGORITHM = "HS256"
TOKEN_EXPIRY_HOURS = 24


class AuthError(Exception):
    pass


def _get_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY", "kanban-dev-secret-change-in-production")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": now + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "iat": now,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as error:
        raise AuthError("Token has expired.") from error
    except jwt.InvalidTokenError as error:
        raise AuthError("Invalid token.") from error
