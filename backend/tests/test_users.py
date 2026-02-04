import pytest
from httpx import AsyncClient
from fastapi import status
from app.models import User


class TestUsersEndpoints:
    """Test suite for /users endpoints."""

    @pytest.mark.asyncio
    async def test_get_me_without_auth(self, client: AsyncClient):
        """Test that /users/me returns 401 without authentication."""
        response = await client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_me_with_invalid_token(self, client: AsyncClient):
        """Test that /users/me returns 401 with invalid token."""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_me_with_valid_auth(
        self, authenticated_client: AsyncClient, test_user: User
    ):
        """Test that /users/me returns the current user when authenticated."""
        response = await authenticated_client.get("/users/me")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["username"] == test_user.username
        assert data["id"] == test_user.id
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self, client: AsyncClient):
        """Test that multiple users are properly isolated."""
        # Register first user
        response1 = await client.post(
            "/auth/register",
            json={
                "username": "user1",
                "password": "password1",
                "email": "cool.otter@aol.com",
                "private": True,
            },
        )
        assert response1.status_code == status.HTTP_200_OK

        # Register second user
        response2 = await client.post(
            "/auth/register",
            json={
                "username": "user2",
                "password": "password2",
                "email": "grizz.bear@aol.com",
                "private": False,
            },
        )
        assert response2.status_code == status.HTTP_200_OK

        # Login as user1
        login1 = await client.post(
            "/auth/login",
            data={"username": "user1", "password": "password1"},
        )
        token1 = login1.json()["access_token"]

        # Login as user2
        login2 = await client.post(
            "/auth/login",
            data={"username": "user2", "password": "password2"},
        )
        token2 = login2.json()["access_token"]

        # Verify user1 gets their own data
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "user1"

        # Verify user2 gets their own data
        response = await client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "user2"
