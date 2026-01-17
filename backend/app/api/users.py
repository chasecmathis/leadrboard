from fastapi import APIRouter, Depends
from app.models import User, UserResponse
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me", response_model=UserResponse, description="Returns the current logged in user"
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # This code only runs if the token is valid
    return UserResponse(id=current_user.id, username=current_user.username)


@router.delete(
    "/me", response_model=UserResponse, description="Deletes the current logged in user"
)
async def delete_users_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await session.delete(current_user)
    await session.commit()
    return UserResponse(id=current_user.id, username=current_user.username)
