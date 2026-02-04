import pytest
from httpx import AsyncClient
from fastapi import status
from app.models import User, CommentResponse, UpdateCommentRequest
from app.common_types import FollowStatus
from sqlmodel.ext.asyncio.session import AsyncSession


class TestInteractionsEndpoints:
    """Test suite for /interactions endpoints."""

    @pytest.mark.asyncio
    async def test_like_review_different_user_success(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        follow_request_factory,
    ):
        """Test that liking a review works."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        response = await authenticated_client.post(f"/reviews/{review.id}/like")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user_id"] == test_user.id
        assert response.json()["review_id"] == review.id

        await test_session.refresh(review)
        assert len(review.likes) == 1
        assert review.likes[0].user_id == test_user.id
        assert review.likes[0].review_id == review.id

    @pytest.mark.asyncio
    async def test_like_review_not_found(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test liking a review that doesn't exist."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )

        response = await authenticated_client.post(f"/reviews/{review.id + 1}/like")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        await test_session.refresh(review)
        assert len(review.likes) == 0

    @pytest.mark.asyncio
    async def test_like_review_duplicate(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        like_factory,
        follow_request_factory,
    ):
        """Test that liking a review that has already been liked."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)
        # Create a test like
        await like_factory(review.id, test_user.id)

        response = await authenticated_client.post(f"/reviews/{review.id}/like")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        await test_session.refresh(review)
        assert len(review.likes) == 1

    @pytest.mark.asyncio
    async def test_unlike_review(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        like_factory,
        follow_request_factory,
    ):
        """Test unliking a review."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)
        # Create a test like
        await like_factory(review.id, test_user.id)

        # Test unliking a review
        response = await authenticated_client.delete(f"/reviews/{review.id}/like")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        await test_session.refresh(review)
        assert len(review.likes) == 0

    @pytest.mark.asyncio
    async def test_unlike_review_not_found(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test unliking a review that doesn't exist."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )

        response = await authenticated_client.delete(f"/reviews/{review.id + 1}/like")
        assert response.status_code == status.HTTP_404_NOT_FOUND

        await test_session.refresh(review)
        assert len(review.likes) == 0

    @pytest.mark.asyncio
    async def test_unlike_review_not_liked(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        follow_request_factory,
    ):
        """Test unliking a review that isn't liked."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        response = await authenticated_client.delete(f"/reviews/{review.id}/like")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        await test_session.refresh(review)
        assert len(review.likes) == 0

    @pytest.mark.asyncio
    async def test_get_likes(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        like_factory,
        follow_request_factory,
    ):
        """Test getting likes."""
        # Create users
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        user3 = await user_factory("user3", "password123", "grizz.bear@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        # Create test likes
        await like_factory(review.id, test_user.id)
        await like_factory(review.id, user3.id)

        response = await authenticated_client.get(f"/reviews/{review.id}/likes")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_create_comment(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        follow_request_factory,
    ):
        """Test creating a comment."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        json_request = {
            "text": "Very cool game!",
            "parent_comment_id": None,
        }
        response = await authenticated_client.post(
            f"/reviews/{review.id}/comments", json=json_request
        )
        assert response.status_code == status.HTTP_201_CREATED

        await test_session.refresh(review)
        assert len(review.comments) == 1
        assert review.comments[0].text == "Very cool game!"

    @pytest.mark.asyncio
    async def test_get_review_comments(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        comment_factory,
        follow_request_factory,
    ):
        """Test getting review comments."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a third user to post a comment with
        user3 = await user_factory("user3", "password123", "grizz.bear@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        # Create dummy comments
        comment1 = await comment_factory(review.id, test_user.id, "Good review!", None)
        comment2 = await comment_factory(
            review.id, test_user.id, "Good review part 2!", None
        )
        comment3 = await comment_factory(
            review.id, user3.id, "Awesome sauce", comment1.id
        )

        response = await authenticated_client.get(f"/reviews/{review.id}/comments")
        assert response.status_code == status.HTTP_200_OK
        response_model = [CommentResponse(**c) for c in response.json()]

        assert len(response_model) == 3
        assert response_model[0].text == comment1.text
        assert response_model[1].text == comment2.text
        assert response_model[2].text == comment3.text

    @pytest.mark.asyncio
    async def test_update_comment(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_session: AsyncSession,
        user_factory,
        game_factory,
        review_factory,
        comment_factory,
        follow_request_factory,
    ):
        """Test updating a comment."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        # Create dummy comments
        comment1 = await comment_factory(review.id, test_user.id, "Good review!", None)

        json_request = UpdateCommentRequest(
            text="This is my edited comment!"
        ).model_dump()
        response = await authenticated_client.put(
            f"/comments/{comment1.id}", json=json_request
        )
        assert response.status_code == status.HTTP_200_OK

        previous_updated_at = comment1.updated_at
        await test_session.refresh(comment1)

        assert comment1.text == json_request["text"]
        assert comment1.updated_at != previous_updated_at
        assert comment1.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_comment_unauthorized(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        comment_factory,
        follow_request_factory,
    ):
        """Test updating a comment with an unauthorized user."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)

        # Create dummy comments
        comment1 = await comment_factory(
            review.id, user2.id, "This is my review!", None
        )

        json_request = UpdateCommentRequest(
            text="This is my edited comment!"
        ).model_dump()
        response = await authenticated_client.put(
            f"/comments/{comment1.id}", json=json_request
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_delete_comment(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_session: AsyncSession,
        user_factory,
        game_factory,
        review_factory,
        comment_factory,
        follow_request_factory,
    ):
        """Test deleting a comment."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Add follower/following
        await follow_request_factory(test_user.id, user2.id, FollowStatus.ACCEPTED)
        # Create dummy comments
        comment1 = await comment_factory(review.id, test_user.id, "Good review!", None)

        response = await authenticated_client.delete(f"/comments/{comment1.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        await test_session.refresh(review)
        assert len(review.comments) == 0
