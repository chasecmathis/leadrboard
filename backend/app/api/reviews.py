from fastapi import APIRouter, Depends, HTTPException, status
from app.models import (
    User,
    CreateReviewRequest,
    Review,
    Game,
    ReviewResponse,
)
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _check_user_interaction_auth(
    current_user: User, target_user: User, target_review: Review
):
    # Check that the current user is following the review's user, the user is public, or it is the current user
    if (
        (current_user.id != target_review.user_id)
        and current_user.id not in target_user.followers
        and target_user.private
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to interact with this review",
        )


@router.post(
    "/",
    response_model=ReviewResponse,
    description="Create a review for a given game",
)
async def create_review(
    review_request: CreateReviewRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the game exists
    result = await session.exec(select(Game).where(Game.id == review_request.game_id))
    target_game = result.first()
    if not target_game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game for this review not found",
        )

    # Check that the user doesn't already have a review for the game
    if any(r.game_id == review_request.game_id for r in current_user.reviews):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a review for this game",
        )

    # Create a review for this game
    review = Review(
        game_id=review_request.game_id,
        user_id=current_user.id,
        rating=review_request.rating,
        review_text=review_request.review_text,
        playtime=review_request.playtime,
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)

    # Return enhanced response with counts
    return ReviewResponse(
        id=review.id,
        game_id=review.game_id,
        user_id=review.user_id,
        username=current_user.username,
        rating=review.rating,
        review_text=review.review_text,
        playtime=review.playtime,
        created_at=review.created_at,
        like_count=0,
        comment_count=0,
        user_has_liked=False,
    )


@router.get(
    "/{review_id}",
    response_model=ReviewResponse,
    description="Get a single review with like and comment counts",
)
async def get_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Get the review
    result = await session.exec(select(Review).where(Review.id == review_id))
    review = result.first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user, review)

    # Get like count
    like_count = len(review.likes)

    # Get comment count
    comment_count = len(review.comments)

    # Check if current user has liked this review
    user_has_liked = any(like.user_id == current_user.id for like in review.likes)

    return ReviewResponse(
        id=review.id,
        game_id=review.game_id,
        user_id=review.user_id,
        username=review.user.username,
        rating=review.rating,
        review_text=review.review_text,
        playtime=review.playtime,
        created_at=review.created_at,
        like_count=like_count,
        comment_count=comment_count,
        user_has_liked=user_has_liked,
    )


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a review",
)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Get the review
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if target_review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to perform this action",
        )

    await session.delete(target_review)
    await session.commit()
