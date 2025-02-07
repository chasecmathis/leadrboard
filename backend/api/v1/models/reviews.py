from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from api.v1.models.common import PyObjectId


class ReviewBase(BaseModel):
    game_id: str
    rating: float = Field(ge=0, le=5)
    review_text: Optional[str] = None
    played_date: datetime
    play_time: Optional[float] = None


class ReviewCreate(ReviewBase):
    pass


class Review(ReviewBase):
    id: PyObjectId = Field(..., alias="_id")
    user_id: PyObjectId
    created_at: datetime
    likes: List[PyObjectId] = Field(default_factory=list)

    class Config:
        from_attributes = True
