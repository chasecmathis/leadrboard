from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from config import get_settings
from database import Database
from api.v1.models.users import User

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = timedelta(minutes=15)
):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, settings.algorithm)
    return encoded_jwt


async def verify_token(token: str, db: Database):
    try:
        payload = jwt.decode(
            token, get_settings().secret_key, [get_settings().algorithm]
        )
        username = payload.get("sub")
        if not username:
            return None

        user = await db.get_db().users.find_one({"username": username})
        return User(**user)
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    return pwd_context.hash(password)
