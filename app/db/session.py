"""Database session utilities for async SQLAlchemy with PostgreSQL."""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ..config import settings

# Async engine using asyncpg driver
# Adjust DATABASE_URL for asyncpg driver.
# Railway (and many providers) supply a URL starting with "postgres://".
# SQLAlchemy with asyncpg expects "postgresql+asyncpg://".
# We replace either prefix accordingly.
# Determine final async URL, falling back to SQLite if DATABASE_URL points to a local Postgres that may be unavailable
raw_url = settings.database_url
if raw_url.startswith('postgres://') or raw_url.startswith('postgresql://'):
    # Check for localhost addresses which often indicate a missing external DB in container
    if 'localhost' in raw_url or '127.0.0.1' in raw_url or '::1' in raw_url:
        # Use SQLite fallback for local development / missing DB
        raw_url = 'sqlite+aiosqlite:///./emag_scraper.db'

if raw_url.startswith('sqlite'):
    async_url = raw_url
elif raw_url.startswith('postgres://'):
    async_url = raw_url.replace('postgres://', 'postgresql+asyncpg://', 1)
else:
    async_url = raw_url.replace('postgresql://', 'postgresql+asyncpg://', 1)

engine: AsyncEngine = create_async_engine(
    async_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if async_url.startswith('sqlite') else {},
)

# Session factory
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def get_db() -> AsyncSession:
    """FastAPI dependency that provides an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
