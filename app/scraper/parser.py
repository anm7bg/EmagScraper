"""Resilient CSS selector-based parser.

Rule: NEVER rely on a single selector.
Every field is extracted by trying multiple selectors in order; the first match wins.
"""

import re
from typing import List, Optional, Dict, Any
from playwright.async_api import Page, ElementHandle


# ---------------------------------------------------------------------------
# Selector sets — ordered by reliability (most stable first)
# ---------------------------------------------------------------------------

PRODUCT_CARD_SELECTORS = [
    ".card-item",  # Updated primary selector for product cards on emag.bg
    "[data-product-id]",
    ".product-grid-item",
    ".listing-item",
    "div[data-product]",
    ".product-outer-wrapper",  # kept as fallback for older layout
]

TITLE_SELECTORS = [
    ".product-name",
    "h2.product-name",
    ".card-title",
    "[data-testid='product-title']",
    "a[href*='/products/']",
    "a.card-alt",  # new selector for emag card titles
    "h2",
    "h3",
]

TITLE_LINK_SELECTORS = [
    "a.product-title",
    "a[href*='/products/']",
    "a.card-link",
    "a.card-alt",  # new selector for emag card title link
    ".product-url",
    "a[href]",
]

PRICE_SELECTORS = [
    ".product-new-price",
    ".price",
    "[data-testid='product-price']",
    ".money",
    ".pricing",
    ".current-price",
    "span[class*='price']",
]

IMAGE_SELECTORS = [
    ".product-image img",
    ".thumbnail img",
    ".card-img-top",
    "img[data-src]",
    "img[src]",
    "img",
]

# Category breadcrumbs selectors – try several common patterns
CATEGORY_SELECTORS = [
    ".breadcrumbs a",
    ".breadcrumb a",
    ".product-breadcrumb a",
    ".product-breadcrumbs a",
]

# ---------------------------------------------------------------------------
# Helper – try multiple selectors until one yields a result
# ---------------------------------------------------------------------------


async def _first_match(page: Page, selectors: List[str], context: Optional[Page | ElementHandle] = None) -> Optional[Any]:
    """Return the first non‑None result from evaluating each selector.

    Tries *page.locator(sel).first* (if context is a Page) or *context.query_selector(sel)*
    when a specific element is passed.  Returns the matching Playwright element or None.
    """
    base = context if context else page
    for sel in selectors:
        try:
            if isinstance(base, Page):
                locator = base.locator(sel).first
                if await locator.count() > 0:
                    return locator
            else:
                elem = await base.query_selector(sel)
                if elem:
                    return elem
        except Exception:
            continue
    return None


async def _all_matches(page: Page, selectors: List[str]) -> List[Any]:
    """Return all elements matching ANY of the given selectors (used for product cards)."""
    results = []
    for sel in selectors:
        try:
            elems = await page.query_selector_all(sel)
            if elems:
                results.extend(elems)
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# Public extraction helpers
# ---------------------------------------------------------------------------


async def extract_product_cards(page: Page) -> List[ElementHandle]:
    """Return all product card elements using multiple fallback selectors."""
    cards: List[ElementHandle] = []
    for sel in PRODUCT_CARD_SELECTORS:
        try:
            found = await page.query_selector_all(sel)
            if found:
                cards = found
                break
        except Exception:
            continue
    # Deduplicate by inner HTML to avoid double‑counting
    seen = set()
    unique = []
    for c in cards:
        html = await c.inner_html()
        if html not in seen:
            seen.add(html)
            unique.append(c)
    return unique


async def extract_title(card: ElementHandle) -> str:
    for sel in TITLE_SELECTORS:
        try:
            elem = await card.query_selector(sel)
            if elem:
                text = (await elem.inner_text()).strip()
                if text:
                    return text
        except Exception:
            continue
    return ""


async def extract_product_url(card: ElementHandle, base_url: str) -> str:
    for sel in TITLE_LINK_SELECTORS:
        try:
            elem = await card.query_selector(sel)
            if elem:
                href = await elem.get_attribute("href")
                if href:
                    return href if href.startswith("http") else base_url + href
        except Exception:
            continue
    return ""


async def extract_price(card: ElementHandle) -> tuple[float, str]:
    """Return (numeric_price, raw_price_string)."""
    for sel in PRICE_SELECTORS:
        try:
            elem = await card.query_selector(sel)
            if elem:
                raw = (await elem.inner_text()).strip()
                if raw:
                    price = _parse_price(raw)
                    return price, raw
        except Exception:
            continue
    return 0.0, ""


async def extract_image_url(card: ElementHandle, base_url: str) -> str:
    for sel in IMAGE_SELECTORS:
        try:
            elem = await card.query_selector(sel)
            if elem:
                url = (
                    await elem.get_attribute("data-src")
                    or await elem.get_attribute("src")
                    or await elem.get_attribute("data-lazy-src")
                )
                if url:
                    return url if url.startswith("http") else base_url + url
        except Exception:
            continue
    return ""


async def extract_categories(card: ElementHandle) -> List[str]:
    """Return a list of category names from breadcrumbs (if any)."""
    for sel in CATEGORY_SELECTORS:
        try:
            elems = await card.query_selector_all(sel)
            if elems:
                categories = []
                for e in elems:
                    txt = (await e.inner_text()).strip()
                    if txt:
                        categories.append(txt)
                if categories:
                    return categories
        except Exception:
            continue
    return []


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _parse_price(raw: str) -> float:
    """Convert a localized price string like '799,99 лв.' to float 799.99."""
    cleaned = re.sub(r"[^\d,.\s]", "", raw)
    cleaned = cleaned.strip()
    # Remove spaces (thousands separators)
    cleaned = cleaned.replace(" ", "")
    # Strip trailing dots/commas that are punctuation, not part of the number
    cleaned = cleaned.rstrip(".").rstrip(",")
    # If both comma and dot exist, decide which is decimal separator
    if "," in cleaned and "." in cleaned:
        # Assume last separator is decimal (e.g., 1,234.56 or 1.234,56)
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0
