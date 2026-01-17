import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.models import User
from sqlmodel.ext.asyncio.session import AsyncSession


class TestInteractionsEndpoints:
    """Test suite for /interactions endpoints."""

    @pytest.mark.asyncio
    async def test_like_review_different_user_success(
        self,
        authenticated_client: TestClient,
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

        response = authenticated_client.post(f"/reviews/{review.id}/like")
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
        authenticated_client: TestClient,
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

        response = authenticated_client.post(f"/reviews/{review.id}/like")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["user_id"] == test_user.id
        assert response.json()["review_id"] == review.id

        await test_session.refresh(review)
        assert len(review.likes) == 1
        assert review.likes[0].user_id == test_user.id
        assert review.likes[0].review_id == review.id
