from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from core.dependencies import get_current_user
from config import get_settings
from database import db
from api.v1.models.users import User

router = APIRouter()
settings = get_settings()


@router.post("/currently_playing/{game_id}")
async def set_currently_playing(game_id: str, user: User = Depends(get_current_user)):
    result = await db.get_db().users.update_one(
        {"_id": user.id}, {"$set": {"currently_playing": game_id}}
    )

    print(result.matched_count)

    return {"message": "Successfully updated currently playing game"}


@router.delete("/currently_playing")
async def remove_currently_playing(user: User = Depends(get_current_user)):
    await db.get_db().users.update_one(
        {"_id": user.id}, {"$set": {"currently_playing": None}}
    )

    return {"message": "Successfully removed currently playing game"}


@router.post("/leadrboard")
async def update_leadrboard(
    game_ids: List[str], user: User = Depends(get_current_user)
):

    if len(game_ids) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Leadrboard must be no more than 5 games",
        )

    await db.get_db().users.update_one(
        {"_id": user.id}, {"$set": {"leadrboard": game_ids}}
    )

    return {"message": "Successfully updated leadrboard"}
