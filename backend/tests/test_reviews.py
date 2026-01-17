import pytest
from fastapi.testclient import TestClient
from fastapi import status
from app.models import User
from sqlmodel.ext.asyncio.session import AsyncSession


class TestReviewsEndpoints:
    """Test suite for /reviews endpoints."""

    def test_create_review_without_auth(self, client: TestClient):
        """Test that /reviews/ returns 401 without authentication."""
        json_request = {
            "game_id": 1,
            "rating": 6.9,
            "review_text": "Cool game",
            "playtime": 120,
        }
        response = client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_create_review_game_not_found(
        self,
        authenticated_client: TestClient,
    ):
        """Test that /reviews/ returns 404 when game doesn't exist."""
        json_request = {
            "game_id": 1,
            "rating": 6.9,
            "review_text": "Cool game",
            "playtime": 120,
        }
        response = authenticated_client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Game for this review not found"

    @pytest.mark.asyncio
    async def test_create_review_duplicate(
        self,
        authenticated_client: TestClient,
        test_session: AsyncSession,
        test_user: User,
        game_factory,
        review_factory,
    ):
        """Test that /reviews/ blocks a user from making two reviews on the same game."""
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        await review_factory(
            game.id, test_user.id, rating=9.6, review_text="Cool game", playtime=120
        )

        json_request = {
            "game_id": game.id,
            "rating": 6.9,
            "review_text": "Cool game",
            "playtime": 120,
        }
        response = authenticated_client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "You already have a review for this game"

        await test_session.refresh(test_user)
        assert len(test_user.reviews) == 1
        assert test_user.reviews[0].game_id == game.id

    @pytest.mark.asyncio
    async def test_create_review_success(
        self,
        authenticated_client: TestClient,
        test_session: AsyncSession,
        test_user: User,
        game_factory,
    ):
        """Test that /reviews/ correctly creates a review."""
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        json_request = {
            "game_id": game.id,
            "rating": 6.9,
            "review_text": "Cool game",
            "playtime": 120,
        }
        response = authenticated_client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["user_id"] == test_user.id
        assert response.json()["game_id"] == game.id

        await test_session.refresh(test_user)
        assert len(test_user.reviews) == 1
        assert test_user.reviews[0].game_id == game.id

    @pytest.mark.asyncio
    async def test_create_two_reviews_success(
        self,
        authenticated_client: TestClient,
        test_session: AsyncSession,
        test_user: User,
        game_factory,
    ):
        """Test that /reviews/ correctly creates a review."""
        # Create a test game
        game1 = await game_factory("Test Game 1", "A test game summary", 1)
        game2 = await game_factory("Test Game 2", "A test game summary", 2)

        # Make first review
        json_request = {
            "game_id": game1.id,
            "rating": 6.9,
            "review_text": "Cool game",
            "playtime": 120,
        }
        response = authenticated_client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_200_OK

        # Make second review
        json_request = {
            "game_id": game2.id,
            "rating": 7.1,
            "review_text": "Cooler game",
            "playtime": 120,
        }
        response = authenticated_client.post("/reviews", json=json_request)
        assert response.status_code == status.HTTP_200_OK

        await test_session.refresh(test_user)
        assert len(test_user.reviews) == 2
        assert test_user.reviews[0].game_id == game1.id
        assert test_user.reviews[1].game_id == game2.id

    @pytest.mark.asyncio
    async def test_delete_review(
        self,
        authenticated_client: TestClient,
        test_session: AsyncSession,
        test_user: User,
        game_factory,
        review_factory,
    ):
        """Test that deleting a review works."""
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)
        # Create a test review
        review = await review_factory(
            game.id, test_user.id, rating=9.6, review_text="Cool game", playtime=120
        )
        response = authenticated_client.delete(f"/reviews/{review.id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

        await test_session.refresh(test_user)
        assert len(test_user.reviews) == 0
