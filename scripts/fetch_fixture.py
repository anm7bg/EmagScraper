"""Fetch real HTML from Emag search page and save as test fixture."""

import asyncio
from playwright.async_api import async_playwright


async def fetch_and_save():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        url = "https://www.emag.bg/search/nike/"
        print(f"Fetching {url} ...")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open("tests/fixtures/emag_sample.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Saved {len(html)} bytes to tests/fixtures/emag_sample.html")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(fetch_and_save())
