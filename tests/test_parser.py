import pytest
from playwright.async_api import async_playwright
from app.scraper.parser import (
    extract_title,
    extract_product_url,
    extract_price,
    extract_image_url,
    extract_product_cards,
    _parse_price,
)

# ---------------------------------------------------------------------------
# Tests for price‑parsing utility (pure, no browser needed)
# ---------------------------------------------------------------------------


def test_parse_price_various_formats():
    assert _parse_price("799,99 лв.") == pytest.approx(799.99)
    assert _parse_price("1,234.56 €") == pytest.approx(1234.56)
    assert _parse_price("€ 89.90") == pytest.approx(89.90)
    assert _parse_price("2 499,00 лв.") == pytest.approx(2499.00)
    assert _parse_price("") == 0.0
    assert _parse_price("invalid") == 0.0


# ---------------------------------------------------------------------------
# Mock HTML snippets for a single product card
# ---------------------------------------------------------------------------

MOCK_CARD_HTML = """
<div class="product-outer-wrapper" data-product-id="123">
    <a class="product-title" href="/products/nike-123">Nike Air Max 90</a>
    <span class="product-new-price">799,99 лв.</span>
    <div class="product-image">
        <img src="https://example.com/nike.jpg" alt="Nike">
    </div>
</div>
"""

MOCK_PAGE_HTML = f"""
<html>
<head><title>Test</title></head>
<body>
{MOCK_CARD_HTML}
{MOCK_CARD_HTML.replace('123', '456').replace('Nike Air Max 90', 'Nike Air Force 1')}
</body>
</html>
"""


@pytest.mark.asyncio
async def test_extract_product_cards():
    """Parser should find cards using multiple fallback selectors."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_PAGE_HTML)
        cards = await extract_product_cards(page)
        assert len(cards) == 2, f"Expected 2 cards, got {len(cards)}"
        await browser.close()


@pytest.mark.asyncio
async def test_extract_title():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_CARD_HTML)
        card = (await extract_product_cards(page))[0]
        title = await extract_title(card)
        assert title == "Nike Air Max 90", f"Got '{title}'"
        await browser.close()


@pytest.mark.asyncio
async def test_extract_product_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_CARD_HTML)
        card = (await extract_product_cards(page))[0]
        url = await extract_product_url(card, "https://www.emag.bg")
        assert url == "https://www.emag.bg/products/nike-123", f"Got '{url}'"
        await browser.close()


@pytest.mark.asyncio
async def test_extract_price():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_CARD_HTML)
        card = (await extract_product_cards(page))[0]
        price, raw = await extract_price(card)
        assert price == pytest.approx(799.99), f"Price mismatch: {price}"
        assert raw == "799,99 лв.", f"Raw price mismatch: {raw}"
        await browser.close()


@pytest.mark.asyncio
async def test_extract_image_url():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(MOCK_CARD_HTML)
        card = (await extract_product_cards(page))[0]
        img_url = await extract_image_url(card, "https://www.emag.bg")
        assert img_url == "https://example.com/nike.jpg", f"Got '{img_url}'"
        await browser.close()


@pytest.mark.asyncio
async def test_fallback_selectors():
    """When the primary selector is missing, fallbacks should still work."""
    html_missing_primary = """
    <div class="card-item">
        <h2 class="product-name">Fallback Title</h2>
        <span class="money">199.99</span>
    </div>
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_missing_primary)
        cards = await extract_product_cards(page)
        assert len(cards) > 0, "Fallback selector failed to find card"
        title = await extract_title(cards[0])
        assert title == "Fallback Title", f"Fallback title extraction failed: {title}"
        price, _ = await extract_price(cards[0])
        assert price == pytest.approx(199.99), "Fallback price extraction failed"
        await browser.close()
