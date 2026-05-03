"""Playwright-based scraper for Emag search results using resilient parser."""

from typing import List, Dict
import asyncio
import random
import time
from playwright.async_api import async_playwright
from app.config import settings
from app.scraper.parser import (
    extract_product_cards,
    extract_title,
    extract_product_url,
    extract_price,
    extract_image_url,
    extract_categories,
)

EMAG_DOMAINS = {
    "emag.bg": "https://www.emag.bg",
}

STORE_ALIASES = {
    "emag.bg": "emag",
}


async def scrape_emag(keyword: str, store: str = "emag.bg", page: int = 1) -> List[Dict]:
    """Scrape Emag search results and return products in the specified format."""
    if store not in EMAG_DOMAINS:
        raise ValueError(f"Unsupported store: {store}. Only emag.bg is supported.")

    base_url = EMAG_DOMAINS[store]
    search_url = f"{base_url}/search/{keyword}/p{page}/"
    products: List[Dict] = []

    # Retry loop with random delay
    for attempt in range(3):
        try:
            # Random delay before each attempt
            await asyncio.sleep(random.uniform(1, 3))

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=settings.headless)
                context = await browser.new_context(user_agent=settings.user_agent)
                page_obj = await context.new_page()

                try:
                    await page_obj.goto(search_url, wait_until="networkidle", timeout=30000)
                    # Wait enough time for dynamic content to render
                    await page_obj.wait_for_timeout(3000)

                    cards = await extract_product_cards(page_obj)

                    for card in cards:
                        try:
                            title = await extract_title(card)
                            url = await extract_product_url(card, base_url)
                            price, raw_price = await extract_price(card)
                            img_url = await extract_image_url(card, base_url)
                            categories = await extract_categories(card)

                            products.append({
                                "title": title,
                                "categories": categories,
                                "price": price,
                                "raw_price": raw_price,
                                "url": url,
                                "store": STORE_ALIASES.get(store, store),
                                "img_url": img_url,
                            })
                        except Exception as e:
                            print(f"Skipping product due to error: {e}")
                            continue
                finally:
                    await browser.close()
            # Success - break out of retry loop
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Scrape attempt {attempt + 1} failed: {e}, retrying...")

    return products
