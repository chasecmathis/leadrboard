from fastapi import APIRouter, Depends, HTTPException, status

from app.models import (
    User,
    Review,
    Like,
    Comment,
    LikeResponse,
    CreateCommentRequest,
    UpdateCommentRequest,
    CommentResponse,
)
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from datetime import datetime

router = APIRouter(tags=["Interactions"])


def _check_user_interaction_auth(current_user: User, target_user: User):
    follower_ids = set(f.follower_id for f in target_user.followers)
    # Check that the current user is following the review's user, the user is public, or it is the current user
    if (
        current_user.id != target_user.id
        and current_user.id not in follower_ids
        and target_user.private
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to interact with this review",
        )


# ============ LIKES ENDPOINTS ============


@router.post(
    "/reviews/{review_id}/like",
    response_model=LikeResponse,
    status_code=status.HTTP_201_CREATED,
    description="Like a review",
)
async def like_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the review exists
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == target_review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user)

    # Check if user already liked this review
    result = await session.exec(
        select(Like).where(
            Like.review_id == review_id and Like.user_id == current_user.id
        )
    )
    existing_like = result.first()
    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already liked this review",
        )

    # Create the like
    like = Like(review_id=review_id, user_id=current_user.id)
    session.add(like)
    await session.commit()
    await session.refresh(like)

    return LikeResponse(
        review_id=like.review_id,
        user_id=like.user_id,
        created_at=like.created_at,
    )


@router.delete(
    "/reviews/{review_id}/like",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Unlike a review",
)
async def unlike_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the review exists
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == target_review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user)

    # Check if like exists
    result = await session.exec(
        select(Like).where(
            Like.review_id == review_id and Like.user_id == current_user.id
        )
    )
    existing_like = result.first()
    if not existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this review",
        )

    await session.delete(existing_like)
    await session.commit()


@router.get(
    "/reviews/{review_id}/likes",
    response_model=list[LikeResponse],
    description="Get all likes for a review",
)
async def get_review_likes(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Check that the review exists
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == target_review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user)

    # Get all likes for the review
    likes = target_review.likes

    return [
        LikeResponse(
            review_id=like.review_id,
            user_id=like.user_id,
            created_at=like.created_at,
        )
        for like in likes
    ]


# ============ COMMENTS ENDPOINTS ============


@router.post(
    "/reviews/{review_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    description="Create a comment on a review",
)
async def create_comment(
    review_id: int,
    comment_request: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the review exists
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == target_review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user)

    # If parent_comment_id is provided, check that it exists and belongs to the same review
    if comment_request.parent_comment_id:
        result = await session.exec(
            select(Comment).where(Comment.id == comment_request.parent_comment_id)
        )
        parent_comment = result.first()
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )
        if parent_comment.review_id != review_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment does not belong to this review",
            )

    # Create the comment
    comment = Comment(
        review_id=review_id,
        user_id=current_user.id,
        text=comment_request.text,
        parent_comment_id=comment_request.parent_comment_id,
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)

    return CommentResponse(
        id=comment.id,
        review_id=comment.review_id,
        user_id=comment.user_id,
        username=current_user.username,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get(
    "/reviews/{review_id}/comments",
    response_model=list[CommentResponse],
    description="Get all comments for a review",
)
async def get_review_comments(
    review_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Check that the review exists
    result = await session.exec(select(Review).where(Review.id == review_id))
    target_review = result.first()
    if not target_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    result = await session.exec(select(User).where(User.id == target_review.user_id))
    target_user: User = result.first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found",
        )

    _check_user_interaction_auth(current_user, target_user)

    comments = []

    for comment in target_review.comments:
        comments.append(
            CommentResponse(
                id=comment.id,
                review_id=comment.review_id,
                user_id=comment.user_id,
                username=comment.user.username,
                parent_comment_id=comment.parent_comment_id,
                text=comment.text,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
        )

    return comments


@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
    description="Update a comment",
)
async def update_comment(
    comment_id: int,
    update_request: UpdateCommentRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the comment exists
    result = await session.exec(select(Comment).where(Comment.id == comment_id))
    target_comment = result.first()
    if not target_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Check ownership
    if target_comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to edit this comment",
        )

    # Update the comment
    target_comment.text = update_request.text
    target_comment.updated_at = datetime.now()
    session.add(target_comment)
    await session.commit()
    await session.refresh(target_comment)

    return CommentResponse(
        id=target_comment.id,
        review_id=target_comment.review_id,
        user_id=target_comment.user_id,
        username=current_user.username,
        parent_comment_id=target_comment.parent_comment_id,
        text=target_comment.text,
        created_at=target_comment.created_at,
        updated_at=target_comment.updated_at,
    )


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Delete a comment",
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Check that the comment exists
    result = await session.exec(select(Comment).where(Comment.id == comment_id))
    target_comment = result.first()
    if not target_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    # Check ownership
    if target_comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to delete this comment",
        )

    await session.delete(target_comment)
    await session.commit()
