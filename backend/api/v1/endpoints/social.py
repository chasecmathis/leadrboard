from fastapi import APIRouter, Depends, HTTPException, status
from core.dependencies import get_current_user
from typing import List
from config import get_settings
from database import db
from api.v1.models.users import User
from api.v1.models.follow_requests import FollowRequest
from api.v1.models.reviews import Review
from api.v1.models.common import PyObjectId
from datetime import datetime, timezone

router = APIRouter()
settings = get_settings()


@router.post("/{user_id}/follow")
async def follow_user(
    user_id: PyObjectId, current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot follow yourself"
        )

    target_user = await db.get_db().users.find_one({"_id": user_id})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    target_user = User(**target_user)

    if (
        user_id not in current_user.following
        and current_user.id not in target_user.followers
    ):
        if target_user.is_private:
            existing_follow_request = await db.get_db().follow_requests.find_one(
                {"from_user_id": current_user.id}, {"to_user_id": user_id}
            )
            if existing_follow_request:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already requested to follow this user",
                )

            follow_request = {
                "from_user_id": current_user.id,
                "to_user_id": user_id,
                "created_at": datetime.now(timezone.utc),
            }
            await db.get_db().follow_requests.insert_one(follow_request)
            return {"message": "Follow request sent"}
        else:
            await db.get_db().users.update_one(
                {"_id": current_user.id}, {"$push": {"following": user_id}}
            )

            await db.get_db().users.update_one(
                {"_id": user_id}, {"$push": {"followers": current_user.id}}
            )
            return {"message": "Successfully followed user"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already following this user",
        )


@router.post("/{user_id}/unfollow")
async def unfollow_user(
    user_id: PyObjectId, current_user: User = Depends(get_current_user)
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot unfollow yourself",
        )

    target_user = await db.get_db().users.find_one({"_id": user_id})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    target_user = User(**target_user)

    if user_id in current_user.following and current_user.id in target_user.followers:
        await db.get_db().users.update_one(
            {"_id": current_user.id}, {"$pull": {"following": user_id}}
        )

        await db.get_db().users.update_one(
            {"_id": user_id}, {"$pull": {"followers": current_user.id}}
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not following this user",
        )

    return {"message": "Successfully unfollowed user"}


@router.get("/follow-requests", response_model=List[FollowRequest])
async def get_follow_requests(
    current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 10
):
    follow_requests = (
        await db.get_db()
        .follow_requests.find({"to_user_id": current_user.id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    return [FollowRequest(**follow_request) for follow_request in follow_requests]


@router.post("/follow_request/{request_id}/approve")
async def approve_follow_request(
    request_id: PyObjectId, user: User = Depends(get_current_user)
):
    follow_request = await db.get_db().follow_requests.find_one({"_id": request_id})
    if not follow_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found"
        )

    follow_request = FollowRequest(**follow_request)

    if follow_request.to_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are unauthorized to approve this request",
        )

    await db.get_db().users.update_one(
        {"_id": follow_request.from_user_id},
        {"$push": {"following": follow_request.to_user_id}},
    )

    await db.get_db().users.update_one(
        {"_id": follow_request.to_user_id},
        {"$push": {"followers": follow_request.from_user_id}},
    )

    await db.get_db().follow_requests.delete_one({"_id": request_id})

    return {"message": "Follow request successfully approved"}


@router.post("/follow_request/{request_id}/reject")
async def reject_follow_request(
    request_id: PyObjectId, user: User = Depends(get_current_user)
):
    follow_request = await db.get_db().follow_requests.find_one({"_id": request_id})
    if not follow_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found"
        )

    follow_request = FollowRequest(**follow_request)

    if follow_request.to_user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are unauthorized to reject this request",
        )

    await db.get_db().follow_requests.delete_one({"_id": request_id})

    return {"message": "Follow request successfully rejected"}


@router.get("/feed", response_model=List[Review])
async def get_feed(
    current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 10
):
    reviews = (
        await db.get_db()
        .reviews.find({"user_id": {"$in": current_user.following}})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
        .to_list(limit)
    )

    return [Review(**review) for review in reviews]
