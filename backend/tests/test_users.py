from fastapi.testclient import TestClient
from fastapi import status
from app.models import User


class TestUsersEndpoints:
    """Test suite for /users endpoints."""

    def test_get_me_without_auth(self, client: TestClient):
        """Test that /users/me returns 401 without authentication."""
        response = client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    def test_get_me_with_invalid_token(self, client: TestClient):
        """Test that /users/me returns 401 with invalid token."""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    def test_get_me_with_valid_auth(
        self, authenticated_client: TestClient, test_user: User
    ):
        """Test that /users/me returns the current user when authenticated."""
        response = authenticated_client.get("/users/me")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["username"] == test_user.username
        assert data["id"] == test_user.id
        assert "hashed_password" not in data

    def test_multiple_users_isolation(self, client: TestClient):
        """Test that multiple users are properly isolated."""
        # Register first user
        response1 = client.post(
            "/auth/register",
            json={"username": "user1", "password": "password1"},
        )
        assert response1.status_code == status.HTTP_200_OK

        # Register second user
        response2 = client.post(
            "/auth/register",
            json={"username": "user2", "password": "password2"},
        )
        assert response2.status_code == status.HTTP_200_OK

        # Login as user1
        login1 = client.post(
            "/auth/login",
            data={"username": "user1", "password": "password1"},
        )
        token1 = login1.json()["access_token"]

        # Login as user2
        login2 = client.post(
            "/auth/login",
            data={"username": "user2", "password": "password2"},
        )
        token2 = login2.json()["access_token"]

        # Verify user1 gets their own data
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "user1"

        # Verify user2 gets their own data
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "user2"
