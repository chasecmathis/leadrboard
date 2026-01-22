import jwt

from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from app.core.config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.models import User
from sqlmodel import select

oauth2scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Initialize hashing (Argon2)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings().SECRET_KEY, algorithm=settings().ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings().SECRET_KEY, algorithms=[settings().ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    statement = select(User).where(User.username == username)
    result = await session.exec(statement)
    user = result.one_or_none()
    if user is None:
        raise credentials_exception

    return user
