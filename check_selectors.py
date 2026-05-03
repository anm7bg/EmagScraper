"""Check which selectors from debug.py still work on emag.bg and show first product card HTML."""
import asyncio
from playwright.async_api import async_playwright

async def main():
    from app.routers.debug import SELECTORS
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.emag.bg/search/nike/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        print("=== Checking SELECTORS from debug.py ===")
        for sel in SELECTORS:
            try:
                count = await page.locator(sel).count()
                status = "OK" if count > 0 else "MISSING"
                print(f"  [{status}] {sel}: {count}")
                if count > 0 and ('title' in sel or 'price' in sel or 'img' in sel):
                    sample = await page.locator(sel).first.inner_text()
                    print(f"    Sample text: {sample[:100]}")
            except Exception as e:
                print(f"  [ERROR] {sel}: {e}")
        # Show HTML of first product card using query_selector
        try:
            card = await page.query_selector('.card-item')
            if card:
                html = await card.inner_html()
                print("\n=== First .card-item HTML snippet (first 800 chars) ===")
                print(html[:800])
            else:
                print("No .card-item found")
        except Exception as e:
            print(f"Error retrieving first card: {e}")
        await browser.close()

asyncio.run(main())
