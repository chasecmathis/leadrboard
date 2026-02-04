from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.db.session import get_session
from app.models import User, AuthResponse, RegisterUserRequest, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", description="Register a new user", response_model=UserResponse
)
async def register(
    user: RegisterUserRequest, session: AsyncSession = Depends(get_session)
):
    # Check if user exists
    statement = select(User).where(User.username == user.username)
    result = await session.exec(statement)
    if result.first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    new_user = User(
        username=user.username,
        hashed_password=hash_password(user.password.get_secret_value()),
        email=user.email,
        private=user.private,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserResponse(id=new_user.id, username=new_user.username)


@router.post("/login", description="Login a new user", response_model=AuthResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # Simple login logic
    statement = select(User).where(User.username == form_data.username)
    result = await session.exec(statement)
    user = result.one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings().ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return AuthResponse(access_token=access_token)
