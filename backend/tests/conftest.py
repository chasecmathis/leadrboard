import pytest
import pytest_asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from httpx import AsyncClient, ASGITransport
from fastapi import status
from app.main import app
from app.db.session import get_session
from app.models import User, Follow, Game, Review, Like
from app.core.security import hash_password
from app.common_types import FollowStatus


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite database engine for testing."""
    # Use in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    return engine


@pytest_asyncio.fixture
async def setup_database(test_engine):
    """Set up the database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
def session_maker(test_engine):
    """Create a session maker for the test database."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_session(
    session_maker, setup_database
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(setup_database, session_maker) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client that uses the test database."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    # Override the get_session dependency
    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True
    ) as test_client:
        yield test_client

    # Clear overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(user_factory) -> User:
    """Create a test user in the database."""
    return await user_factory(username="test_user", password="password123")


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient, test_user: User) -> str:
    """Get an authentication token for the test user."""
    response = await client.post(
        "/auth/login",
        data={
            "username": "test_user",
            "password": "password123",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, auth_token: str) -> AsyncClient:
    """Create a client with authentication headers."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {auth_token}",
    }
    return client


@pytest.fixture
def user_factory(test_session: AsyncSession):
    """Factory to create multiple test users."""

    async def _create_user(username: str, password: str) -> User:
        user = User(
            username=username,
            hashed_password=hash_password(password),
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def follow_request_factory(test_session: AsyncSession):
    """Factory to create an authenticated followers request."""

    async def _create_follow_request(
        follower_user_id, followed_user_id, status=FollowStatus.PENDING
    ):
        follow_request = Follow(
            followed_id=followed_user_id, follower_id=follower_user_id, status=status
        )
        test_session.add(follow_request)
        await test_session.commit()
        await test_session.refresh(follow_request)
        return follow_request

    return _create_follow_request


@pytest.fixture
def game_factory(test_session: AsyncSession):
    """Factory to create test games."""

    async def _create_game(title: str, summary: str, igdb_id: int) -> Game:
        game = Game(
            title=title,
            summary=summary,
            igdb_id=igdb_id,
        )
        test_session.add(game)
        await test_session.commit()
        await test_session.refresh(game)
        return game

    return _create_game


@pytest.fixture
def review_factory(test_session: AsyncSession):
    """Factory to create test reviews."""

    async def _create_review(
        game_id: int,
        user_id: int,
        rating: float,
        review_text: str,
        playtime: Optional[int],
    ) -> Review:
        review = Review(
            game_id=game_id,
            user_id=user_id,
            rating=rating,
            review_text=review_text,
            playtime=playtime,
        )
        test_session.add(review)
        await test_session.commit()
        await test_session.refresh(review)
        return review

    return _create_review


@pytest.fixture
def like_factory(test_session: AsyncSession):
    """Factory to create test likes."""

    async def _create_like(review_id: int, user_id: int):
        like = Like(
            review_id=review_id,
            user_id=user_id,
        )
        test_session.add(like)
        await test_session.commit()
        await test_session.refresh(like)
        return like

    return _create_like
