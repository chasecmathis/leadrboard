from typing import Sequence

from fastapi import APIRouter, Depends, Query
from app.models import User, Review, FeedItemResponse
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get(
    "/",
    response_model=list[FeedItemResponse],
    description="Get personalized feed of reviews from followed users",
)
async def get_feed(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(
        default=20, ge=1, le=100, description="Number of items to return"
    ),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """
    Get a personalized feed of reviews from users you follow.
    Reviews are sorted by creation date (most recent first).
    """
    followed_users = current_user.following

    # If no users to fetch from, return empty feed
    if not followed_users:
        return []

    user_ids_to_fetch = set(user.followed_id for user in followed_users)

    # Query reviews from followed users (and optionally current user)
    reviews_statement = (
        select(Review)
        .where(Review.user_id.in_(user_ids_to_fetch))
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    reviews_result = await session.exec(reviews_statement)
    reviews: Sequence[Review] = reviews_result.all()

    # Build feed items with like and comment counts
    feed_items = []
    for review in reviews:
        # Get like count
        like_count = len(review.likes)

        # Get comment count (using imported Comment model)
        comment_count = len(review.comments)

        # Check if current user has liked this review
        has_liked = current_user.id in [r.user_id for r in review.likes]

        feed_items.append(
            FeedItemResponse(
                review_id=review.id,
                game_id=review.game.id,
                game_title=review.game.title,
                game_cover_image=review.game.cover_image,
                user_id=review.user.id,
                username=review.user.username,
                rating=review.rating,
                review_text=review.review_text,
                playtime=review.playtime,
                created_at=review.created_at,
                like_count=like_count,
                comment_count=comment_count,
                user_has_liked=has_liked,
            )
        )

    return feed_items
