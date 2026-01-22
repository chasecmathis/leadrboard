from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from typing import AsyncGenerator
from functools import lru_cache

# Use the asyncpg driver for PostgreSQL
@lru_cache()
def get_async_engine():
    return create_async_engine(settings().DATABASE_URL, future=True)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    AsyncSessionLocal = async_sessionmaker(
        bind=get_async_engine(), class_=AsyncSession, expire_on_commit=False
    )
    async with AsyncSessionLocal() as session:
        yield session
