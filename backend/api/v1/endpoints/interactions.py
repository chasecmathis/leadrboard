from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user
from config import get_settings
from database import db
from api.v1.models.users import User
from api.v1.models.reviews import Review
from api.v1.models.common import PyObjectId
from api.v1.models.comments import Comment, CommentCreate

router = APIRouter()
settings = get_settings()


@router.post("/reviews/{review_id}/comments", response_model=Comment)
async def create_comment(
    review_id: PyObjectId,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
):
    review = await db.get_db().reviews.find_one({"_id": review_id})
    review = Review(**review)
    _verify_authorized_review(review, current_user)

    comment_dict = comment.dict()
    comment_dict["review_id"] = review_id
    comment_dict["user_id"] = current_user.id
    comment_dict["created_at"] = datetime.now(timezone.utc)

    result = await db.get_db().comments.insert_one(comment_dict)
    created_comment = await db.get_db().comments.find_one({"_id": result.inserted_id})

    return Comment(**created_comment)


@router.get("/reviews/{review_id}/comments")
async def get_comments(
    review_id: PyObjectId,
    user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
):
    review = await db.get_db().reviews.find_one({"_id": review_id})
    review = Review(**review)
    _verify_authorized_review(review, user)

    comments = await (
        db.get_db()
        .comments.find({"review_id": review_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    return [Comment(**comment) for comment in comments]


@router.post("/reviews/{review_id}/like")
async def like_review(review_id: PyObjectId, user: User = Depends(get_current_user)):
    review = await db.get_db().reviews.find_one({"_id": review_id})
    review = Review(**review)
    _verify_authorized_review(review, user)

    if user.id in review.likes:
        await db.get_db().reviews.update_one(
            {"_id": review_id}, {"$pull": {"likes": user.id}}
        )
        return {"message": "Successfully unliked review"}
    else:
        await db.get_db().reviews.update_one(
            {"_id": review_id}, {"$push": {"likes": user.id}}
        )
        return {"message": "Successfully liked review"}


def _verify_authorized_review(review: Review, user: User):
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
        )

    if review.user_id not in user.following and review.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to access this review",
        )
