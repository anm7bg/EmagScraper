"""Inspect live page title selectors with UTF-8 handling."""
import asyncio

from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.emag.bg/search/nike/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # Get first product card
        card = await page.query_selector(".card-item")
        if card:
            html = await card.inner_html()

            # Convert to UTF-8 for processing
            html_utf8 = html.encode('utf-8', errors='ignore').decode('utf-8')
            print("Card HTML (UTF-8 encoded, first 2000 chars): ")
            print(html_utf8[:2000])

            # Check possible title selectors
            selectors_to_try = [
                ".product-name",                # From snapshot
                "h2.product-name",              # From original scraper
                "a[href*='/products/']",        # Link selector
                ".card-alt",                     # Alternative
                "[class*='title']"               # Generic fallback
            ]

            for sel in selectors_to_try:
                count = await page.locator(sel).count()
                if count > 0:
                    print(f"\nSelector '{sel}': {count} matches\nHTML: {await page.locator(sel).first.inner_text()[:100]}")

        else:
            print("No .card-item found")

        await browser.close()

asyncio.run(main())
