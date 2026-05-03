import pytest
import asyncio
from playwright.async_api import async_playwright
from app.routers.debug import SELECTORS

@pytest.mark.asyncio
async def test_selectors_working():
    """Ensure each selector defined in the scraper matches at least one element on a live Emag page.
    This catches DOM changes before production.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        url = "https://www.emag.bg/search/nike/"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        # give a short pause for lazy‑loaded elements
        await page.wait_for_timeout(2000)
        for selector in SELECTORS:
            count = await page.locator(selector).count()
            assert count > 0, f"Selector '{selector}' matched no elements"
        await browser.close()
