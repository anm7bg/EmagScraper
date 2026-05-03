#!/usr/bin/env python
"""
Script to query and display product details from the EmagScrapper database.
Also creates tables if they don't exist (for SQLite).
"""
import asyncio
import sys
import os

# Add the app directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models.product import Product, PriceHistory
from app.db.session import AsyncSessionLocal, engine, Base
from sqlalchemy import select, inspect


async def ensure_tables():
    """Create tables if they don't exist."""
    async with engine.begin() as conn:
        # Use run_sync to run the synchronous metadata.create_all
        def create_tables(sync_conn):
            # Check if tables exist by inspecting
            inspector = inspect(sync_conn)
            existing_tables = inspector.get_table_names()
            needed = {'products', 'price_history', 'scrape_jobs'}
            if not needed.issubset(set(existing_tables)):
                print("Creating missing tables...")
                Base.metadata.create_all(sync_conn)
            else:
                print("Tables already exist.")
        await conn.run_sync(create_tables)


async def main():
    """Query and display all products from the database."""
    # Ensure tables exist
    await ensure_tables()

    print("Connecting to database and fetching products...")

    async with AsyncSessionLocal() as session:
        # Query all products
        result = await session.execute(select(Product))
        products = result.scalars().all()

        if not products:
            print("No products found in the database.")
            return

        print(f"\nFound {len(products)} products:\n")
        print("-" * 80)

        for i, product in enumerate(products, 1):
            print(f"{i}. Title: {product.title}")
            print(f"   Price: {product.price} {product.currency}")
            print(f"   URL: {product.product_url}")
            print(f"   Image URL: {product.image_url or 'N/A'}")
            print(f"   External ID: {product.external_id}")
            print(f"   Store: {product.store}")
            # Categories may be None; show as comma‑separated list if present
            cats = product.categories or []
            if isinstance(cats, (list, tuple)):
                cat_str = ", ".join(cats)
            else:
                cat_str = str(cats)
            print(f"   Categories: {cat_str if cat_str else 'N/A'}")
            print(f"   Scraped At: {product.scraped_at}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
