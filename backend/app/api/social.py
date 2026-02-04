from fastapi import APIRouter, Depends, HTTPException, status
from app.models import User, Follow
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import app.common_types as types

router = APIRouter(prefix="/social", tags=["Social"])


@router.post(
    "/follow/{user_id}",
    response_model=Follow,
    description="Send a follow request to a user",
)
async def send_follow_request(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the user isn't trying to follow themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself"
        )

    # Check that the targeted user exists
    result = await session.exec(select(User).where(User.id == user_id))
    target_user = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user is already followed/sent follow request
    if any(f.follower_id == current_user.id for f in target_user.followers):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already following this user",
        )

    follow_status = (
        types.FollowStatus.PENDING
        if target_user.private
        else types.FollowStatus.ACCEPTED
    )
    # Follow the user
    follow = Follow(
        followed_id=target_user.id,
        follower_id=current_user.id,
        status=follow_status,
    )
    target_user.followers.append(follow)
    session.add(target_user)
    await session.commit()
    await session.refresh(follow)

    return follow


@router.post(
    "/requests/{user_id}/accept",
    response_model=Follow,
    description="Approve a follow request from a user",
)
async def approve_follow_request(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the user isn't trying to approve themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot approve yourself",
        )

    # Check that the targeted user exists
    result = await session.exec(select(User).where(User.id == user_id))
    target_user = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Make sure the user is a follower
    for follower in current_user.followers:
        if follower.follower_id == user_id:
            # Check that the request wasn't already approved
            if follower.status != types.FollowStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This follow request is not pending",
                )
            else:
                follower.status = types.FollowStatus.ACCEPTED
                session.add(follower)
                await session.commit()

                return follower
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="This user does not follow you"
    )


@router.get(
    "/requests",
    response_model=list[Follow],
    description="Get all follow requests for the current user",
)
async def get_follow_requests(
    request_status: types.FollowStatus = None,
    current_user: User = Depends(get_current_user),
):
    if request_status is None:
        return current_user.followers
    return [
        follow for follow in current_user.followers if follow.status == request_status
    ]


@router.post(
    "/requests/{user_id}/remove",
    response_model=Follow,
    description="Remove a follow",
)
async def reject_follow_request(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the user isn't trying to approve themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot approve yourself",
        )

    # Check that the targeted user exists
    result = await session.exec(select(User).where(User.id == user_id))
    target_user = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Make sure the user is a follower
    for follower in current_user.followers:
        if follower.follower_id == user_id:
            await session.delete(follower)
            await session.commit()

            return follower
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="This user does not follow you"
    )
