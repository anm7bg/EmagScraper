# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python scraping API for Emag e-commerce platform (only emag.bg). FastAPI backend uses Playwright for headless scraping, PostgreSQL for persistent storage. Supports single and batch scraping (for cron/automation). Data is consumed by a Next.js frontend and a WordPress integration via REST API.

## Tech Stack

- **Python 3.x** + **FastAPI** (API framework)
- **Playwright** (headless browser scraping)
- **PostgreSQL** (required persistent storage, not optional)
- **SQLAlchemy** + **Alembic** (ORM and migrations)

## Environment

- Claude Code LLM is configured via OpenRouter (`openrouter/free`) in `.claude/settings.local.json` — app secrets (DB credentials, etc.) go in a `.env` file (never committed).
- Windows environment (PowerShell) — use `venv\Scripts\activate` for virtual environment.

## Architecture

### Scraper API (this repository)

```
app/
├── main.py            # FastAPI entry point
├── config.py          # Settings from environment variables
├── schemas.py         # Pydantic response schemas (ProductOut, ScrapeResponse)
├── routers/           # API route handlers
│   └── scrape.py     # GET /scrape (direct), POST /scrape (job), GET /scrape/{id}, POST /scrape/batch
├── models/            # SQLAlchemy models + Pydantic schemas
│   ├── product.py    # Product, PriceHistory (not yet stored)
│   └── scrape_job.py # ScrapeJob + request/response schemas (includes pages property)
├── scraper/           # Playwright scraping logic
│   ├── emag.py       # Emag-specific selectors and parsing (only emag.bg)
│   └── browser.py    # Shared Playwright setup/teardown
└── db/                # Database session, init, migrations
    └── session.py     # Async SQLAlchemy engine + session
```

### Key Design Decisions

- **GET /scrape?keyword=...&page=...** returns scraped products directly (synchronous, no job tracking).
- **POST /scrape** triggers async scraping job (keyword, store fixed to emag.bg, `pages` property controls how many result pages to scrape); returns job ID.
- **GET /scrape/{job_id}** returns job status (pending/running/success/failed) and products_found count.
- **POST /scrape/batch** (for cron/automation) accepts a list of keywords, creates a job per keyword, each job scrapes `pages` pages.
- **`pages` property**: present in ScrapeRequest, ScrapeBatchRequest, and ScrapeJob models. Controls how many Emag search-result pages are scraped per job (default 1).
- **PostgreSQL schema**: `products` (id, title, price, currency, image_url, product_url, store, external_id), `price_history` (product_id, price, scraped_at), `scrape_jobs` (id, keyword, store, status, pages, created_at, finished_at, error, products_found)
- **Playwright** runs in headless Chromium; must handle Emag's dynamic content (lazy loading, infinite scroll)
- **Rate limiting**: respect robots.txt, add delays between requests, randomize user agents

### Clients (separate repositories)

- **Next.js**: Consumes `/products` endpoints, displays searchable product grid with price history charts
- **WordPress**: Plugin or theme integration via WP REST API, periodically fetches and caches product data

## Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Run (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head

# Tests
pytest -xvs
pytest tests/test_scraper.py::test_extract_products  # single test

# Lint
ruff check app/
```

## Notes

- Scaffolding complete: FastAPI app, Playwright scraper, PostgreSQL models, and batch endpoint are in place.
- Only **emag.bg** is supported (emag.ro removed per user request).
- Emag may block aggressive scraping; implement user-agent rotation and request throttling from day one.
- Store scraped data idempotently (upsert on external_id + store) to avoid duplicates.
- See `API_DOCS.md` for full endpoint documentation, request/response schemas, and cron usage examples.
