from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
import asyncio
import os

from alembic import context

# Alembic Config
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models to register them with Base metadata
from app.db.session import Base
from app.models.product import Product, PriceHistory  # noqa: F401
from app.models.scrape_job import ScrapeJob  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_name="postgresql",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Override sqlalchemy.url from environment variable
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Fallback to SQLite if DATABASE_URL points to localhost (common in containers without DB)
        if 'localhost' in db_url or '127.0.0.1' in db_url or '::1' in db_url:
            db_url = 'sqlite:///./emag_scraper.db'
        else:
            # Convert postgres:// to postgresql+asyncpg://
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif "postgresql://" in db_url and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        config.set_main_option("sqlalchemy.url", db_url)

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn, target_metadata=target_metadata
            )
        )
        async with connection.begin():
            await connection.run_sync(lambda conn: context.run_migrations())

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
