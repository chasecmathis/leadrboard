import pytest
from httpx import AsyncClient
from fastapi import status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import User, Follow
import app.common_types as types


class TestSocialEndpoints:
    """Test suite for /social endpoints."""

    @pytest.mark.asyncio
    async def test_send_follow_request_without_auth(self, client: AsyncClient):
        """Test that /social/follow/{user_id} returns 401 without authentication."""
        response = await client.post("/social/follow/0")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_send_follow_request_to_current_user(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_session: AsyncSession,
    ):
        """Test that /social/follow/{user_id} returns 400 if it gets sent to the current user."""
        response = await authenticated_client.post(f"/social/follow/{test_user.id}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "You cannot follow yourself"

        result = await test_session.exec(select(Follow))

        follows = result.all()
        assert len(follows) == 0, "There should be no follow records"

    @pytest.mark.asyncio
    async def test_send_follow_request_to_missing_user(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        test_session: AsyncSession,
    ):
        """Test that /social/follow/{user_id} returns 404 if it gets sent to a missing user."""
        response = await authenticated_client.post(f"/social/follow/{test_user.id + 1}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "User not found"

        result = await test_session.exec(select(Follow))

        follows = result.all()
        assert len(follows) == 0, "There should be no follow records"

    @pytest.mark.asyncio
    async def test_send_follow_request_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        test_session: AsyncSession,
    ):
        """Test that a follow request is successfully created in the database."""
        # Create a second user to follow
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Send follow request
        response = await authenticated_client.post(f"/social/follow/{user2.id}")
        assert response.status_code == status.HTTP_200_OK

        # Check that a Follow record was created with the correct status
        result = await test_session.exec(
            select(Follow).where(
                Follow.follower_id == test_user.id, Follow.followed_id == user2.id
            )
        )
        follow = result.one_or_none()

        assert follow is not None, "Follow record should exist in database"
        assert follow.follower_id == test_user.id
        assert follow.followed_id == user2.id
        assert follow.status == types.FollowStatus.PENDING

        assert follow.created_at is not None

    @pytest.mark.asyncio
    async def test_duplicate_follow_request(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        test_session: AsyncSession,
    ):
        """Test that sending a duplicate follow request is handled properly."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Send first follow request
        response1 = await authenticated_client.post(f"/social/follow/{user2.id}")
        assert response1.status_code == status.HTTP_200_OK

        # Send duplicate follow request
        response2 = await authenticated_client.post(f"/social/follow/{user2.id}")
        # Should return 400
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

        # Verify only one Follow record exists
        result = await test_session.exec(
            select(Follow).where(
                Follow.follower_id == test_user.id, Follow.followed_id == user2.id
            )
        )
        follows = result.all()
        assert len(follows) == 1, "Should only have one follow record"

    @pytest.mark.asyncio
    async def test_approve_follow_request_success(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        follow_request_factory,
        test_session: AsyncSession,
    ):
        """Test that sending a duplicate follow request is handled properly."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Insert a pending follow request into the DB
        await follow_request_factory(user2.id, test_user.id)

        # Approve follow request
        approve_response = await authenticated_client.post(
            f"/social/requests/{user2.id}/accept"
        )
        assert approve_response.status_code == status.HTTP_200_OK

        # Check that a Follow record was approved with the correct status
        result = await test_session.exec(
            select(Follow).where(
                Follow.follower_id == user2.id, Follow.followed_id == test_user.id
            )
        )
        follow = result.one_or_none()

        assert follow is not None, "Follow record should exist in database"
        assert follow.status == types.FollowStatus.ACCEPTED
        assert follow.created_at is not None

        await test_session.refresh(test_user)

        # Verify test_user's followers list includes user2
        assert len(test_user.followers) == 1
        assert test_user.followers[0].follower_id == user2.id
        assert test_user.followers[0].status == types.FollowStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_approve_follow_request_not_pending(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        follow_request_factory,
        test_session: AsyncSession,
    ):
        """Test that sending a duplicate follow request is handled properly."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Insert a follow request into the DB
        await follow_request_factory(
            user2.id, test_user.id, types.FollowStatus.ACCEPTED
        )

        # Approve follow request
        approve_response = await authenticated_client.post(
            f"/social/requests/{user2.id}/accept"
        )
        assert approve_response.status_code == status.HTTP_400_BAD_REQUEST
        assert approve_response.json()["detail"] == "This follow request is not pending"

        # Check that a Follow record was approved with the correct status
        result = await test_session.exec(
            select(Follow).where(
                Follow.follower_id == user2.id, Follow.followed_id == test_user.id
            )
        )
        follow = result.one_or_none()

        assert follow is not None, "Follow record should exist in database"
        assert follow.status == types.FollowStatus.ACCEPTED

    @pytest.mark.asyncio
    async def test_send_follow_request_updates_user_relationships(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        test_session: AsyncSession,
    ):
        """Test that follow relationships are properly reflected on both users."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Send follow request
        response = await authenticated_client.post(f"/social/follow/{user2.id}")
        assert response.status_code == status.HTTP_200_OK

        # Refresh users to get updated relationships
        await test_session.refresh(test_user)
        await test_session.refresh(user2)

        # Verify test_user's following list includes user2
        assert len(test_user.following) == 1
        assert test_user.following[0].followed_id == user2.id

        # Verify user2's followers list includes test_user
        assert len(user2.followers) == 1
        assert user2.followers[0].follower_id == test_user.id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "follow_status", [types.FollowStatus.ACCEPTED, types.FollowStatus.PENDING]
    )
    async def test_reject_follow_request(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        follow_request_factory,
        test_session: AsyncSession,
        follow_status: types.FollowStatus,
    ):
        """Test rejecting a follow request."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Insert a pending follow request into the DB
        await follow_request_factory(user2.id, test_user.id, follow_status)

        # Reject follow request
        approve_response = await authenticated_client.post(
            f"/social/requests/{user2.id}/remove"
        )
        assert approve_response.status_code == status.HTTP_200_OK

        # Refresh users to get updated relationships
        await test_session.refresh(test_user)
        await test_session.refresh(user2)

        assert len(user2.following) == 0
        assert len(test_user.followers) == 0

    @pytest.mark.asyncio
    async def test_reject_follow_request_not_following(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        user_factory,
        test_session: AsyncSession,
    ):
        """Test rejecting a follow request."""
        user2 = await user_factory("user2", "password123", "cool.otter@aol.com")

        # Reject follow request
        approve_response = await authenticated_client.post(
            f"/social/requests/{user2.id}/remove"
        )
        assert approve_response.status_code == status.HTTP_400_BAD_REQUEST
        assert approve_response.json()["detail"] == "This user does not follow you"

        # Refresh users to get updated relationships
        await test_session.refresh(test_user)
        await test_session.refresh(user2)

        assert len(user2.following) == 0
        assert len(test_user.followers) == 0
