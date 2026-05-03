"""Database session utilities for async SQLAlchemy with PostgreSQL."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ..config import settings

# Async engine using asyncpg driver
# Adjust DATABASE_URL for asyncpg driver.
# Railway (and many providers) supply a URL starting with "postgres://".
# SQLAlchemy with asyncpg expects "postgresql+asyncpg://".
# We replace either prefix accordingly.
raw_url = settings.database_url
if raw_url.startswith('postgres://'):
    async_url = raw_url.replace('postgres://', 'postgresql+asyncpg://', 1)
else:
    async_url = raw_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

engine: AsyncEngine = create_async_engine(
    async_url,
    echo=False,
    future=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """FastAPI dependency that provides an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
