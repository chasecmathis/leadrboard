import pytest
from httpx import AsyncClient
from fastapi import status
from app.models import User, FeedItemResponse
from app.common_types import FollowStatus


class TestFeedEndpoints:
    """Test suite for the /feed endpoints."""

    @pytest.mark.asyncio
    async def test_get_feed_empty(self, authenticated_client: AsyncClient):
        """Test getting feed when the user follows no one."""
        response = await authenticated_client.get("/feed/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_feed_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        like_factory,
        comment_factory,
        follow_request_factory,
    ):
        """Test getting feed with reviews from followed users."""
        # Create another user and follow them
        followed_user = await user_factory("followed_guy", "pass123")
        await follow_request_factory(
            follower_user_id=test_user.id,
            followed_user_id=followed_user.id,
            status=FollowStatus.ACCEPTED,
        )

        # Create a game and a review from that followed user
        game = await game_factory("Elden Ring", "GOTY", 123)
        review = await review_factory(
            game.id,
            followed_user.id,
            rating=10,
            review_text="Masterpiece",
            playtime=100,
        )
        await like_factory(review.id, test_user.id)
        await comment_factory(review.id, test_user.id, "Praise the sun!", None)

        response = await authenticated_client.get("/feed/")

        assert response.status_code == status.HTTP_200_OK
        data = [FeedItemResponse(**item) for item in response.json()]
        assert len(data) == 1
        assert data[0].review_id == review.id
        assert data[0].username == followed_user.username
        assert data[0].game_title == game.title
        assert data[0].user_has_liked
        assert data[0].like_count == 1

    @pytest.mark.asyncio
    async def test_feed_pagination(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        game_factory,
        review_factory,
        follow_request_factory,
    ):
        """Test that limit and skip parameters work for the feed."""
        followed_user1 = await user_factory("followed_guy1", "pass123")
        await follow_request_factory(
            test_user.id, followed_user1.id, FollowStatus.ACCEPTED
        )
        followed_user2 = await user_factory("followed_guy2", "pass123")
        await follow_request_factory(
            test_user.id, followed_user2.id, FollowStatus.ACCEPTED
        )

        followed_user3 = await user_factory("followed_guy3", "pass123")
        await follow_request_factory(
            test_user.id, followed_user3.id, FollowStatus.ACCEPTED
        )

        game = await game_factory("Game 1", "Summary", 1)

        # Create 3 reviews
        await review_factory(game.id, followed_user1.id, 5.0, "Review 1", 10)
        await review_factory(game.id, followed_user2.id, 5.0, "Review 2", 10)
        await review_factory(game.id, followed_user3.id, 5.0, "Review 3", 10)

        # Test limit=2
        response = await authenticated_client.get("/feed/", params={"limit": 2})
        assert len(response.json()) == 2

        # Test skip=2
        response = await authenticated_client.get("/feed/", params={"skip": 2})
        assert len(response.json()) == 1

    @pytest.mark.asyncio
    async def test_feed_excludes_unfollowed_users(
        self,
        authenticated_client: AsyncClient,
        user_factory,
        game_factory,
        review_factory,
    ):
        """Test that reviews from users NOT followed do not appear in feed."""
        # Create a user we do NOT follow
        stranger = await user_factory("stranger", "pass123")
        game = await game_factory("Secret Game", "Summary", 999)
        await review_factory(game.id, stranger.id, 1.0, "Don't look at this", 5)

        response = await authenticated_client.get("/feed/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 0
