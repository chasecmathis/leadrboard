from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timezone
from core.dependencies import get_current_user
from database import db
from api.v1.models.reviews import Review, ReviewCreate
from api.v1.models.users import User

router = APIRouter()


@router.post("/", response_model=Review)
async def create_review(review: ReviewCreate, user: User = Depends(get_current_user)):
    existing_review = await db.get_db().reviews.find_one(
        {"game_id": review.game_id, "username": user.username}
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this game",
        )

    review_dict = review.dict()
    review_dict["user_id"] = user.id
    review_dict["created_at"] = datetime.now(timezone.utc)

    result = await db.get_db().reviews.insert_one(review_dict)
    created_review = await db.get_db().reviews.find_one({"_id": result.inserted_id})
    return Review(**created_review)


@router.get("/user/", response_model=List[Review])
async def get_user_reviews(
    user: User = Depends(get_current_user), skip: int = 0, limit: int = 10
):
    reviews = (
        await db.get_db()
        .reviews.find({"user_id": user.id})
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )
    return [Review(**review) for review in reviews]
