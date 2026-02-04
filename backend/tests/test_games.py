import pytest
from httpx import AsyncClient
from fastapi import status
from app.models import User, Game


class TestGamesEndpoints:
    """Test suite for /games endpoints."""

    @pytest.mark.asyncio
    async def test_get_game_without_auth(self, client: AsyncClient):
        """Test that /games/{game_id} returns 401 without authentication."""
        response = await client.get("/games/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_game_with_invalid_token(self, client: AsyncClient):
        """Test that /games/{game_id} returns 401 with invalid token."""
        client.headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/games/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_get_game_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that /games/{game_id} returns 404 when game doesn't exist."""
        response = await authenticated_client.get("/games/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Game not found"

    @pytest.mark.asyncio
    async def test_get_game_success(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/{game_id} returns the correct game when it exists."""
        # Create a test game
        game = await game_factory("Test Game", "A test game summary", 12345)

        response = await authenticated_client.get(f"/games/{game.id}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == game.id
        assert data["title"] == game.title
        assert data["summary"] == game.summary
        assert data["igdb_id"] == game.igdb_id

    @pytest.mark.asyncio
    async def test_get_games_without_auth(self, client: AsyncClient):
        """Test that /games/ returns 401 without authentication."""
        response = await client.get("/games/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_get_games_empty_list(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that /games/ returns an empty list when no games exist."""
        response = await authenticated_client.get("/games/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_games_success(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ returns all games."""
        # Create test games
        game1 = await game_factory("Game 1", "Summary 1", 1001)
        game2 = await game_factory("Game 2", "Summary 2", 1002)
        game3 = await game_factory("Game 3", "Summary 3", 1003)

        response = await authenticated_client.get("/games/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == game1.title
        assert data[1]["title"] == game2.title
        assert data[2]["title"] == game3.title

    @pytest.mark.asyncio
    async def test_get_games_pagination_skip(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ pagination skip parameter works correctly."""
        # Create test games
        await game_factory("Game 1", "Summary 1", 2001)
        await game_factory("Game 2", "Summary 2", 2002)
        game = await game_factory("Game 3", "Summary 3", 2003)

        # Skip first 2 games
        response = await authenticated_client.get("/games?skip=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == game.title

    @pytest.mark.asyncio
    async def test_get_games_pagination_limit(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ pagination limit parameter works correctly."""
        # Create test games
        game1 = await game_factory("Game 1", "Summary 1", 3001)
        game2 = await game_factory("Game 2", "Summary 2", 3002)
        await game_factory("Game 3", "Summary 3", 3003)

        # Limit to 2 games
        response = await authenticated_client.get("/games?limit=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == game1.title
        assert data[1]["title"] == game2.title

    @pytest.mark.asyncio
    async def test_get_games_pagination_skip_and_limit(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ pagination with both skip and limit works correctly."""
        # Create test games
        await game_factory("Game 1", "Summary 1", 4001)
        game2 = await game_factory("Game 2", "Summary 2", 4002)
        game3 = await game_factory("Game 3", "Summary 3", 4003)
        await game_factory("Game 4", "Summary 4", 4004)
        await game_factory("Game 5", "Summary 5", 4005)

        # Skip 1, limit to 2
        response = await authenticated_client.get("/games?skip=1&limit=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == game2.title
        assert data[1]["title"] == game3.title

    @pytest.mark.asyncio
    async def test_get_games_desc(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ with reverse order works correctly."""
        # Create test games
        game1 = await game_factory("Game 1", "Summary 1", 4001)
        game2 = await game_factory("Game 2", "Summary 2", 4002)
        game3 = await game_factory("Game 3", "Summary 3", 4003)

        # Sort in reverse order
        response = await authenticated_client.get("/games?sort_dir=desc")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == game3.title
        assert data[1]["title"] == game2.title
        assert data[2]["title"] == game1.title

    @pytest.mark.asyncio
    async def test_get_games_sort_by(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """Test that /games/ with sort_by works correctly."""
        # Create test games
        game1 = await game_factory("ZGame 1", "Summary 1", 4001)
        game2 = await game_factory("AGame 2", "Summary 2", 4002)
        game3 = await game_factory("MGame 3", "Summary 3", 4003)

        # Sort by title in ascending order
        response = await authenticated_client.get("/games?sort_by=title")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == game2.title
        assert data[1]["title"] == game3.title
        assert data[2]["title"] == game1.title

    @pytest.mark.asyncio
    async def test_get_games_negative_skip(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that /games/ returns 400 with negative skip parameter."""
        response = await authenticated_client.get("/games?skip=-1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid parameters"

    @pytest.mark.asyncio
    async def test_get_games_negative_limit(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that /games/ returns 400 with negative limit parameter."""
        response = await authenticated_client.get("/games?limit=-1")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid parameters"

    @pytest.mark.asyncio
    async def test_discover_personalized_cold_start(
        self,
        authenticated_client: AsyncClient,
        game_factory,
    ):
        """
        Test that a new user (with no reviews) gets the fallback list
        (standard list of games).
        """
        # Create some games so the fallback has something to return
        g1 = await game_factory("Fallout", "RPG", 100)
        g2 = await game_factory("Halo", "FPS", 101)

        # User has 0 reviews
        response = await authenticated_client.get("/games/discover/personalized")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return existing games
        assert len(data) == 2
        titles = [d["title"] for d in data]
        assert g1.title in titles
        assert g2.title in titles

    @pytest.mark.asyncio
    async def test_discover_personalized_with_history(
        self,
        authenticated_client: AsyncClient,
        test_user: User,
        game_factory,
        review_factory,
        user_factory,
    ):
        """
        Test that if User A is similar to User B, User A gets recommended
        games that User B liked.
        """
        # Setup Games
        game_rpg = await game_factory("Skyrim", "RPG", 200)
        game_fps = await game_factory("Doom", "FPS", 201)
        game_target: Game = await game_factory(
            "Witcher", "RPG", 202
        )  # User B likes this, User A hasn't seen it

        # Setup "Neighbor" User (User B)
        user_b = await user_factory("rpg_lover", "password123", "cool.otter@aol.com")

        # Both Current User (A) and User B like Skyrim (High Rating)
        # This makes them "Neighbors" in the vector space
        await review_factory(game_rpg.id, test_user.id, 10.0, "RPG", 360)
        await review_factory(game_rpg.id, user_b.id, 10.0, "RPG 2", 420)

        # User B also loves Witcher, but User A hasn't played it yet.
        # The engine should now recommend Witcher to User A.
        await review_factory(game_target.id, user_b.id, 9.0, "Henry Cavill?", 120)

        # 5. Run Request
        response = await authenticated_client.get("/games/discover/personalized")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # The recommendation engine should prioritize "Witcher"
        recommended_titles = [d["title"] for d in data]

        # Verify we got recommendations
        assert len(data) > 0
        # Ideally, Witcher is in the list
        assert game_target.title in recommended_titles
        # Ideally, Skyrim is NOT in the list (because User A already played it)
        assert game_rpg.title not in recommended_titles
        # Ideally, Doom is not in the list (because User B hasn't played it)
        assert game_fps.title not in recommended_titles
