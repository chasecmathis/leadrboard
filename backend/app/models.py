from pydantic import BaseModel, SecretStr, HttpUrl, EmailStr
from sqlmodel import SQLModel, Field
import app.common_types as types
from datetime import datetime
from app.common_types import HttpUrlType
from sqlmodel import Relationship as SQLModelRelationship
from typing import Any, Optional

# Custom Relationship


def Relationship(
    *,
    back_populates: Optional[str] = None,
    link_model: Optional[Any] = None,
    sa_relationship_kwargs: Optional[dict[str, Any]] = None,
    **kwargs: Any
) -> Any:
    """
    Custom SQLModel Relationship that defaults to 'selectin' loading
    for asyncpg compatibility.
    """
    # Initialize kwargs if None
    if sa_relationship_kwargs is None:
        sa_relationship_kwargs = {}

    # Set selectin as the default loader if not already specified
    sa_relationship_kwargs.setdefault("lazy", "selectin")

    return SQLModelRelationship(
        back_populates=back_populates,
        link_model=link_model,
        sa_relationship_kwargs=sa_relationship_kwargs,
        **kwargs
    )


# SQL Models


class GameGenreLink(SQLModel, table=True):
    game_id: int = Field(title="Game ID", foreign_key="game.id", primary_key=True)
    genre_id: int = Field(title="Genre ID", foreign_key="genre.id", primary_key=True)


class GamePlatformLink(SQLModel, table=True):
    game_id: int = Field(title="Game ID", foreign_key="game.id", primary_key=True)
    platform_id: int = Field(
        title="Platform ID", foreign_key="platform.id", primary_key=True
    )


class Follow(SQLModel, table=True):
    followed_id: int = Field(
        title="Followed ID",
        description="The ID of the followed user",
        primary_key=True,
        foreign_key="user.id",
        ondelete="CASCADE",
    )
    follower_id: int = Field(
        title="Follower ID",
        description="The ID of the user following",
        primary_key=True,
        foreign_key="user.id",
        ondelete="CASCADE",
    )
    status: types.FollowStatus = Field(
        title="Status", description="The status of the follow request"
    )
    created_at: datetime = Field(
        title="Created At",
        description="The date and time of the follow request",
        default_factory=datetime.now,
    )
    # Relationships to User
    followed: "User" = Relationship(
        back_populates="followers",
        sa_relationship_kwargs={
            "foreign_keys": "[Follow.followed_id]",
        },
    )
    follower: "User" = Relationship(
        back_populates="following",
        sa_relationship_kwargs={
            "foreign_keys": "[Follow.follower_id]",
        },
    )


class User(SQLModel, table=True):
    id: Optional[int] = Field(
        title="User ID",
        description="The ID for the given user record",
        default=None,
        primary_key=True,
    )
    username: str = Field(
        title="Username",
        description="Username for the given user",
        unique=True,
        index=True,
    )
    email: EmailStr = Field(
        title="Email",
        description="Email address for the given user",
        unique=True,
    )
    hashed_password: str = Field(
        title="Hashed Password", description="The hashed password of the user"
    )
    private: bool = Field(
        title="Private",
        description="Whether the user's account is private",
    )
    created_at: datetime = Field(
        title="Created At",
        description="The date and time that the user was created",
        default_factory=datetime.now,
    )
    # Users who follow this user
    followers: list["Follow"] = Relationship(
        back_populates="followed",
        cascade_delete=True,
        sa_relationship_kwargs={
            "foreign_keys": "[Follow.followed_id]",
        },
    )
    # Users this user follows
    following: list["Follow"] = Relationship(
        back_populates="follower",
        cascade_delete=True,
        sa_relationship_kwargs={
            "foreign_keys": "[Follow.follower_id]",
        },
    )
    reviews: list["Review"] = Relationship(back_populates="user")
    likes: list["Like"] = Relationship(back_populates="user")
    comments: list["Comment"] = Relationship(back_populates="user")


class Review(SQLModel, table=True):
    id: Optional[int] = Field(title="Review ID", default=None, primary_key=True)
    game_id: Optional[int] = Field(
        title="Game ID",
        description="The ID of the game",
        foreign_key="game.id",
        ondelete="SET NULL",
    )
    user_id: int = Field(
        title="User ID",
        foreign_key="user.id",
        ondelete="CASCADE",
    )
    rating: float = Field(
        ge=0, le=10, title="Rating", description="The review rating of the game"
    )
    review_text: str = Field(
        default="", title="Review Text", description="The review text of the game"
    )
    playtime: Optional[int] = Field(
        title="Playtime",
        description="The amount of time the game was played (in minutes)",
        ge=0,
        default=None,
    )
    created_at: datetime = Field(
        title="Created At",
        description="The date and time that the review was created",
        default_factory=datetime.now,
    )
    game: "Game" = Relationship(back_populates="reviews")
    user: "User" = Relationship(back_populates="reviews")
    likes: list["Like"] = Relationship(back_populates="review")
    comments: list["Comment"] = Relationship(back_populates="review")


class Like(SQLModel, table=True):
    review_id: int = Field(
        title="Review ID",
        description="The ID of the review being liked",
        primary_key=True,
        foreign_key="review.id",
        ondelete="CASCADE",
    )
    user_id: int = Field(
        title="User ID",
        description="The ID of the user who liked the review",
        primary_key=True,
        foreign_key="user.id",
        ondelete="CASCADE",
    )
    created_at: datetime = Field(
        title="Created At",
        description="The date and time the like was created",
        default_factory=datetime.now,
    )
    review: "Review" = Relationship(back_populates="likes")
    user: "User" = Relationship(back_populates="likes")


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(title="Comment ID", default=None, primary_key=True)
    review_id: int = Field(
        title="Review ID",
        description="The ID of the review being commented on",
        foreign_key="review.id",
        ondelete="CASCADE",
        index=True,
    )
    user_id: int = Field(
        title="User ID",
        description="The ID of the user who wrote the comment",
        foreign_key="user.id",
        ondelete="CASCADE",
    )
    parent_comment_id: Optional[int] = Field(
        title="Parent Comment ID",
        description="The ID of the parent comment (for nested/reply comments)",
        foreign_key="comment.id",
        ondelete="CASCADE",
        default=None,
        index=True,
    )
    text: str = Field(
        title="Comment Text",
        description="The text content of the comment",
        min_length=1,
        max_length=500,
    )
    created_at: datetime = Field(
        title="Created At",
        description="The date and time the comment was created",
        default_factory=datetime.now,
    )
    updated_at: Optional[datetime] = Field(
        title="Updated At",
        description="The date and time the comment was last updated",
        default=None,
    )
    review: "Review" = Relationship(back_populates="comments")
    user: "User" = Relationship(back_populates="comments")
    # Self-referential relationship for nested comments
    parent_comment: Optional["Comment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={
            "remote_side": "[Comment.id]",
        },
    )
    replies: list["Comment"] = Relationship(
        back_populates="parent_comment",
        sa_relationship_kwargs={
            "foreign_keys": "[Comment.parent_comment_id]",
        },
    )


class Game(SQLModel, table=True):
    id: Optional[int] = Field(title="Game ID", default=None, primary_key=True)
    title: str = Field(title="Title", description="The title of the game")
    summary: Optional[str] = Field(
        title="Summary", description="The summary of the game"
    )
    release_date: Optional[datetime] = Field(
        title="Release Date", description="The date and time the game was released"
    )
    cover_image: Optional[HttpUrl] = Field(
        title="Cover Image",
        description="A description for the game",
        sa_type=HttpUrlType,
    )
    # External IDs (for API sync)
    igdb_id: int = Field(
        title="IGDB ID",
        description="The corresponding IGDB ID for this game",
        unique=True,
    )
    reviews: list["Review"] = Relationship(back_populates="game")
    genres: list["Genre"] = Relationship(
        back_populates="games", link_model=GameGenreLink
    )
    platforms: list["Platform"] = Relationship(
        back_populates="games", link_model=GamePlatformLink
    )


class Genre(SQLModel, table=True):
    id: Optional[int] = Field(
        title="Genre ID from IGDB", default=None, primary_key=True
    )  # IGDB ID
    name: str = Field(
        title="Genre Name",
        description="Name of the genre from IGDB",
        index=True,
        unique=True,
    )
    games: list["Game"] = Relationship(
        back_populates="genres", link_model=GameGenreLink
    )


class Platform(SQLModel, table=True):
    id: Optional[int] = Field(
        title="Platform ID from IGDB", default=None, primary_key=True
    )  # IGDB ID
    name: str = Field(
        title="Platform Name",
        description="Name of the platform from IGDB",
        index=True,
        unique=True,
    )
    games: list["Game"] = Relationship(
        back_populates="platforms", link_model=GamePlatformLink
    )


# Request/Response Models


class RegisterUserRequest(BaseModel):
    username: str = Field(title="Username", description="Username for the given user")
    password: SecretStr = Field(
        title="Password", description="The plain text password of the user"
    )
    email: EmailStr = Field(
        title="Email",
        description="Email address for the given user",
        unique=True,
    )
    private: bool = Field(
        title="Private",
        description="Whether the user's account is private",
    )


class UserResponse(BaseModel):
    id: int = Field(title="User ID", description="The unique ID of the user")
    username: str = Field(title="Username", description="Username for the given user")


class AuthResponse(BaseModel):
    access_token: str = Field(
        title="Access Token", description="Access token for the authenticated user"
    )
    token_type: str = Field(
        default="bearer",
        title="Token Type",
        description="Token type of the authenticated user",
    )


class CreateReviewRequest(BaseModel):
    game_id: int = Field(
        title="Game ID",
        description="The ID of the game",
    )
    rating: float = Field(
        ge=0, le=10, title="Rating", description="The review rating of the game"
    )
    review_text: str = Field(
        default="", title="Review Text", description="The review text of the game"
    )
    playtime: Optional[int] = Field(
        title="Playtime",
        description="The amount of time the game was played (in minutes)",
        ge=0,
        default=None,
    )


class ReviewResponse(BaseModel):
    id: int = Field(title="Review ID", description="The unique ID of the review")
    game_id: int = Field(title="Game ID", description="The ID of the review's game")
    user_id: int = Field(title="User ID", description="The ID of the review's user")
    username: str = Field(
        title="Username", description="Username for the review's user"
    )
    rating: float = Field(
        title="Rating", description="The review rating given for the game"
    )
    review_text: str = Field(
        title="Review Text", description="The review text provided by the user"
    )
    playtime: Optional[int] = Field(
        title="Playtime",
        description="The amount of time the user has played the game",
        default=None,
    )
    created_at: datetime = Field(
        title="Created At", description="The date and time the review was created"
    )
    like_count: int = Field(
        title="Like Count", description="The number of likes the review has", default=0
    )
    comment_count: int = Field(
        title="Comment Count",
        description="The number of comments the review has",
        default=0,
    )
    user_has_liked: bool = Field(
        title="User Has Liked",
        description="If the user has liked the review",
        default=False,
    )


class LikeResponse(BaseModel):
    review_id: int = Field(title="Review ID", description="The ID of the review")
    user_id: int = Field(title="User ID", description="The user that liked the review")
    created_at: datetime = Field(
        title="Created At", description="The date and time the review was liked"
    )


class CreateCommentRequest(BaseModel):
    text: str = Field(
        title="Comment Text",
        description="The text content of the comment",
        min_length=1,
        max_length=500,
    )
    parent_comment_id: Optional[int] = Field(
        title="Parent Comment ID",
        description="The ID of the parent comment (for nested replies)",
        default=None,
    )


class UpdateCommentRequest(BaseModel):
    text: str = Field(
        title="Comment Text",
        description="The text content of the comment",
        min_length=1,
        max_length=500,
    )


class CommentResponse(BaseModel):
    id: int = Field(title="Comment ID", description="The ID of the comment")
    review_id: int = Field(
        title="Review ID", description="The ID of the review commented on"
    )
    user_id: int = Field(
        title="User ID", description="The ID of the user that commented"
    )
    username: str = Field(
        title="Username", description="Username for the commenting user"
    )
    parent_comment_id: Optional[int] = Field(
        title="Parent Comment ID",
        description="The ID of the parent comment (for nested replies)",
        default=None,
    )
    text: str = Field(
        title="Comment Text", description="The text content of the comment"
    )
    created_at: datetime = Field(
        title="Created At", description="The date and time the comment was created"
    )
    updated_at: Optional[datetime] = Field(
        title="Updated At",
        description="The date and time the comment was updated",
        default=None,
    )


class FeedItemResponse(BaseModel):
    review_id: int = Field(title="Review ID", description="The ID of the review")
    game_id: int = Field(title="Game ID", description="The ID of the game")
    game_title: str = Field(title="Game Title", description="The title of the game")
    game_cover_image: Optional[HttpUrl] = Field(
        title="Game Cover Image",
        description="The cover image of the game",
        default=None,
    )
    user_id: int = Field(
        title="User ID", description="The ID user that made the review"
    )
    username: str = Field(
        title="Username", description="The username user that made the review"
    )
    rating: float = Field(title="Rating", description="The rating for the review")
    review_text: str = Field(
        title="Review Text", description="The text content of the review"
    )
    playtime: Optional[int] = Field(
        title="Playtime",
        default=None,
        description="The amount of the time the game was played",
    )
    created_at: datetime = Field(
        title="Created At", description="When the user created the review"
    )
    like_count: int = Field(
        title="Like Count", description="The number of likes the review has"
    )
    comment_count: int = Field(
        title="Comment Count", description="The number of comments the review has"
    )
    user_has_liked: bool = Field(
        title="User Has Liked", description="If the user has liked the review"
    )
