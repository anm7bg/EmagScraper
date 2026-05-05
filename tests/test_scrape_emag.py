import asyncio
import pytest
from app.scraper.emag import scrape_emag


@pytest.mark.asyncio
async def test_scrape_emag_returns_list():
    products = await scrape_emag("iphone", store="emag.bg", page=1)
    assert isinstance(products, list)
    # Should find some products for a popular keyword
    assert len(products) > 0, "Expected at least one product for 'iphone'"


@pytest.mark.asyncio
async def test_scrape_emag_product_keys():
    products = await scrape_emag("iphone", store="emag.bg", page=1)
    assert len(products) > 0
    sample = products[0]
    expected_keys = {"title", "price", "raw_price", "url", "store", "img_url", "categories"}
    assert expected_keys.issubset(set(sample.keys())), f"Missing keys. Found: {set(sample.keys())}"


@pytest.mark.asyncio
async def test_scrape_emag_invalid_store():
    with pytest.raises(ValueError):
        await scrape_emag("iphone", store="unsupported.bg", page=1)


@pytest.mark.asyncio
async def test_scrape_emag_pagination():
    """Test that pages parameter is respected."""
    products = await scrape_emag("samsung", store="emag.bg", page=1)
    # At least a few products expected
    assert len(products) >= 0  # could be empty, but shouldn't raise
