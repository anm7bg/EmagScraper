"""Inspect a product card to find relevant selectors."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.emag.bg/search/nike/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        # Get first card
        card = await page.query_selector('.card-item')
        if not card:
            print("No card found")
            return
        # Use evaluate to extract info
        data = await page.evaluate("""() => {
            const card = document.querySelector('.card-item');
            if (!card) return null;
            const links = Array.from(card.querySelectorAll('a')).map(a => ({
                href: a.href,
                text: a.innerText.trim().slice(0,50),
                class: a.className
            }));
            const imgs = Array.from(card.querySelectorAll('img')).map(img => ({
                src: img.src,
                class: img.className,
                alt: img.alt
            }));
            const prices = Array.from(card.querySelectorAll('[class*=\"price\"]')).map(el => ({
                text: el.innerText.trim().slice(0,30),
                class: el.className
            }));
            // also get all classes inside card
            const allClasses = new Set();
            card.querySelectorAll('[class]').forEach(el => allClasses.add(el.className));
            return { links, imgs, prices, allClasses: Array.from(allClasses).slice(0,30) };
        }""")
        # Write to file
        with open('inspect_result.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Results written to inspect_result.json")
        await browser.close()

asyncio.run(main())
