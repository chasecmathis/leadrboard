import pytest
from httpx import AsyncClient
from fastapi import status
from app.models import User
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
    ):
        """Test that liking a review works."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )

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
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test liking a review that doesn't exist."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
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
    ):
        """Test that liking a review that has already been liked."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
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
    ):
        """Test unliking a review."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
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
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test unliking a review that doesn't exist."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
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
    ):
        """Test unliking a review that isn't liked."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )

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
        test_session,
    ):
        """Test getting likes."""
        # Create users
        user2 = await user_factory("user2", "password123")
        user3 = await user_factory("user3", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
        # Create test likes
        await like_factory(review.id, test_user.id)
        await like_factory(review.id, user3.id)

        response = await authenticated_client.get(f"/reviews/{review.id}/likes")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_get_create_comment(
        self,
        authenticated_client: AsyncClient,
        test_session: AsyncSession,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test creating a comment."""
        # Create a second user to post a review with
        user2 = await user_factory("user2", "password123")
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, user2.id, rating=9.6, review_text="Cool game", playtime=120
        )
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
