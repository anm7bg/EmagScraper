"""Shared Playwright browser setup."""

from playwright.async_api import async_playwright, Browser, BrowserContext
from app.config import settings


async def get_browser() -> Browser:
    """Launch a Chromium browser instance."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=settings.headless)
    return browser


async def get_context(browser: Browser) -> BrowserContext:
    """Create a browser context with configured user agent."""
    context = await browser.new_context(user_agent=settings.user_agent)
    return context
