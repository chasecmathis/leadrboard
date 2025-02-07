from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from api.v1.models.common import PyObjectId


class FollowRequestBase(BaseModel):
    from_user_id: PyObjectId
    to_user_id: PyObjectId


class FollowRequestCreate(FollowRequestBase):
    pass


class FollowRequest(FollowRequestBase):
    id: PyObjectId = Field(..., alias="_id")
    created_at: datetime

    class Config:
        from_attributes = True
