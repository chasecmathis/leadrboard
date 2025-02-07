from pydantic import BaseModel, Field
from datetime import datetime
from api.v1.models.common import PyObjectId


class CommentBase(BaseModel):
    comment_text: str = Field(..., min_length=1, max_length=500)


class CommentCreate(CommentBase):
    pass


class Comment(CommentBase):
    id: PyObjectId = Field(..., alias="_id")
    review_id: PyObjectId
    user_id: PyObjectId
    created_at: datetime

    class Config:
        from_attributes = True
