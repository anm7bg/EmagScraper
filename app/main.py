"""FastAPI entry point for the Emag Scraper API."""

from fastapi import FastAPI
from app.routers.scrape import router as scrape_router
from app.routers.debug import router as debug_router
from app.config import settings
from app.scraper.emag import scrape_emag
from app.db.session import AsyncSessionLocal, engine, Base

app = FastAPI(
    title="Emag Scraper API",
    version="0.1.0",
    description="FastAPI service that scrapes product data from Emag using Playwright.",
)

app.include_router(scrape_router)
app.include_router(debug_router)


@app.on_event("startup")
async def startup():
    """Create database tables if they don't exist (for PostgreSQL on Railway)."""
    async with engine.begin() as conn:
        def create_tables(sync_conn):
            Base.metadata.create_all(sync_conn)
        await conn.run_sync(create_tables)
    print("Database tables ensured.")


# Simple health check – Railway will call this endpoint to verify the service is up.
@app.get("/healthz")
async def healthz():
    """Very lightweight health check.
    - Verifies the DB connection is alive.
    - Returns HTTP 200 with JSON `{"status": "ok"}` if everything looks fine.
    - If the DB is unreachable returns `{"status": "error", "reason": "..."}`.
    This endpoint avoids launching Playwright, keeping the check fast and cheap.
    """
    try:
        # Perform a minimal DB query to ensure the connection works.
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

# Advanced health check – still available for deeper diagnostics.
@app.get("/health")
async def health_check():
    """Advanced health check:
    - verifies Emag site is reachable
    - attempts to scrape a sample page and count products
    Returns {"status": "ok", "products_found": N}
    or     {"status": "broken", "reason": "..."}
    """
    try:
        # Quick scrape of one page to verify DOM works
        products = await scrape_emag("nike", store="emag.bg", page=1)
        count = len(products)
        if count > 0:
            return {"status": "ok", "products_found": count}
        else:
            return {"status": "broken", "reason": "no products detected"}
    except Exception as e:
        return {"status": "broken", "reason": str(e)}
