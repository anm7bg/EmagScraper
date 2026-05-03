"""Debug endpoints for selector validation."""

from fastapi import APIRouter
from playwright.async_api import async_playwright
from app.config import settings
from app.scraper.emag import EMAG_DOMAINS

router = APIRouter(prefix="/debug", tags=["debug"])

# Selectors used in our scraper (from emag.py)
SELECTORS = [
    ".card-item",                     # Primary product card container (still valid)
    ".product-new-price",            # Price element (primary)
    "h2",                            # Title element (current selector)
    "a[href]",          # Title link selector (generic)
]

DEFAULT_TEST_URL = "https://www.emag.bg/search/nike/"


@router.get("/selectors")
async def debug_selectors(url: str = DEFAULT_TEST_URL):
    """Fetch a page and test which CSS selectors match elements.
    Returns which selectors are working (found >= 1 element) and which are failing.
    """
    results = {"working": [], "failing": []}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=settings.headless)
        context = await browser.new_context(user_agent=settings.user_agent)
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            # Wait a bit for dynamic content
            await page.wait_for_timeout(2000)
            for sel in SELECTORS:
                try:
                    count = await page.locator(sel).count()
                    entry = {"selector": sel, "count": count}
                    if count > 0:
                        results["working"].append(entry)
                    else:
                        results["failing"].append(entry)
                except Exception as e:
                    results["failing"].append({"selector": sel, "count": 0, "error": str(e)})
        finally:
            await browser.close()
    return results
