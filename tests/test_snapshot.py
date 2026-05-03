"""Advanced test that uses a saved HTML snapshot from Emag.

If the live DOM changes, this test will FAIL because the snapshot
no longer matches the expected structure.

The snapshot is stored in tests/fixtures/emag_sample.html.
To refresh it, run:  python scripts/fetch_fixture.py
"""

import pytest
import pathlib
from playwright.async_api import async_playwright
from app.routers.debug import SELECTORS
from app.scraper.parser import extract_product_cards

FIXTURE_PATH = pathlib.Path(__file__).parent / "fixtures" / "emag_sample.html"


@pytest.fixture(scope="module")
def snapshot_html():
    if not FIXTURE_PATH.exists():
        pytest.skip("Snapshot HTML not found. Run: python scripts/fetch_fixture.py")
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_snapshot_selectors(snapshot_html):
    """Load the saved HTML snapshot into a headless browser and verify
    that all our selectors still match at least one element."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(snapshot_html)
        # Give JS a moment (though snapshot is static)
        await page.wait_for_timeout(500)
        for sel in SELECTORS:
            count = await page.locator(sel).count()
            assert count > 0, f"Selector '{sel}' no longer matches in snapshot"
        await browser.close()


@pytest.mark.asyncio
async def test_snapshot_parser_finds_cards(snapshot_html):
    """Verify that the resilient parser can extract product cards from the snapshot."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(snapshot_html)
        cards = await extract_product_cards(page)
        assert len(cards) > 0, "Parser found NO product cards in the snapshot"
        await browser.close()


@pytest.mark.asyncio
async def test_snapshot_product_fields(snapshot_html):
    """Check that the first product card in the snapshot has all required fields."""
    from app.scraper.parser import extract_title, extract_product_url, extract_price, extract_image_url
    from app.routers.debug import EMAG_DOMAINS

    base_url = EMAG_DOMAINS["emag.bg"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(snapshot_html)
        cards = await extract_product_cards(page)
        assert cards, "No cards found"
        card = cards[0]
        title = await extract_title(card)
        assert title, "Title extraction failed on snapshot"
        url = await extract_product_url(card, base_url)
        assert url, "URL extraction failed on snapshot"
        price, raw = await extract_price(card)
        assert price > 0, f"Price extraction failed on snapshot (got {price})"
        img = await extract_image_url(card, base_url)
        assert img, "Image URL extraction failed on snapshot"
        await browser.close()
