import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # FastAPI settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    reload: bool = os.getenv("RELOAD", "True").lower() in ("true", "1", "yes")

    # Database (required PostgreSQL)
    database_url: str = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./emag_scraper.db"
)

    # Playwright
    headless: bool = os.getenv("HEADLESS", "True").lower() in ("true", "1", "yes")
    user_agent: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Scraping behavior
    request_delay: float = float(os.getenv("REQUEST_DELAY", "2.0"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

settings = Settings()
