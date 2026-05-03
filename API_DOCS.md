# Emag Scraper API Documentation

FastAPI service that scrapes product data from Emag (only emag.bg) using Playwright.  
Base URL: `http://localhost:8000`

---

## Endpoints

### 1. GET /scrape  
Scrape products for a keyword and return results directly (synchronous, no job tracking).

**Query Parameters**
| Name     | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| keyword  | str  | yes      | –       | Search term (e.g., "nike") |
| page     | int  | no       | 1       | Page number to scrape |

**Response** `ScrapeResponse`
```json
{
  "products": [
    {
      "title": "Nike Air Max 90",
      "categories": [],
      "price": 799.99,
      "raw_price": "799,99 лв.",
      "url": "https://www.emag.bg/...",
      "store": "emag",
      "img_url": "https://..."
    }
  ]
}
```

**Example**
```bash
curl "http://localhost:8000/scrape?keyword=nike&page=1"
```

---

### 2. POST /scrape  
Start a new scrape job (async by default). Returns a job ID for later status checks.

**Request Body** `ScrapeRequest`
```json
{
  "keyword": "nike",
  "store": "emag.bg",   // fixed, only emag.bg supported
  "pages": 1,            // number of pages to scrape (default 1)
  "async_mode": true      // if false, runs synchronously
}
```

**Response** `ScrapeJobRead` (HTTP 202)
```json
{
  "keyword": "nike",
  "store": "emag.bg",
  "pages": 1,
  "id": 1,
  "status": "pending",
  "created_at": "2026-05-02T12:00:00",
  "finished_at": null,
  "error": null,
  "products_found": 0,
  "async_mode": true
}
```

**Notes**
- `store` is always forced to `"emag.bg"` regardless of request value.
- When `async_mode=true`, the job runs in the background; use endpoint 3 to check status.
- The `pages` property controls how many result pages are scraped (each page ~24 products).

---

### 3. GET /scrape/{job_id}  
Get the status of a scrape job.

**Path Parameters**
| Name   | Type | Description |
|--------|------|-------------|
| job_id | int  | ID of the scrape job |

**Response** `ScrapeJobRead` (same as above)

**Example**
```bash
curl http://localhost:8000/scrape/1
```

---

### 4. POST /scrape/batch  (for cron / automation)
Create multiple scrape jobs for a list of keywords in one call.

**Request Body** `ScrapeBatchRequest`
```json
{
  "keywords": ["nike", "adidas", "puma"],
  "store": "emag.bg",   // fixed
  "pages": 1,           // pages per keyword
  "async_mode": true
}
```

**Response** `List[ScrapeJobRead]` (HTTP 202) – array of created jobs.

**Example**
```bash
curl -X POST http://localhost:8000/scrape/batch \
  -H "Content-Type: application/json" \
  -d '{"keywords":["nike","adidas"],"pages":2}'
```

**Cron Usage**
```bash
# crontab entry to run every day at 2 AM
0 2 * * * curl -X POST http://localhost:8000/scrape/batch \
  -H "Content-Type: application/json" \
  -d '{"keywords":["nike","adidas"],"pages":3,"async_mode":true}'
```

---

## Data Models

### ScrapeRequest (single job)
| Property    | Type | Required | Default | Description |
|-------------|------|----------|---------|-------------|
| keyword     | str  | yes      | –       | Search keyword |
| store       | str  | no       | emag.bg | Fixed to emag.bg |
| pages       | int  | no       | 1       | Number of pages to scrape |
| async_mode  | bool | no       | true    | Run in background |

### ScrapeBatchRequest (batch)
| Property    | Type        | Required | Default | Description |
|-------------|-------------|----------|---------|-------------|
| keywords    | List[str]   | yes      | –       | List of keywords to scrape |
| store       | str         | no       | emag.bg | Fixed to emag.bg |
| pages       | int         | no       | 1       | Pages per keyword |
| async_mode  | bool        | no       | true    | Run jobs in background |

### ScrapeJobRead (job status)
| Property       | Type    | Description |
|----------------|---------|-------------|
| id             | int     | Job ID |
| keyword        | str     | Keyword that was scraped |
| store          | str     | Store (always emag.bg) |
| pages          | int     | Number of pages scraped |
| status         | str     | pending / running / success / failed |
| created_at     | datetime | Job creation time |
| finished_at    | datetime?| When job finished (or null) |
| error          | str?    | Error message if failed |
| products_found | int     | How many products were found |
| async_mode     | bool    | Whether job ran in background |

### ProductOut (scraped product)
| Property  | Type        | Description |
|------------|-------------|-------------|
| title      | str         | Product title |
| categories | List[str]   | Category hierarchy (currently empty) |
| price      | float       | Numeric price (e.g., 799.99) |
| raw_price  | str         | Original price string from site |
| url        | str         | Absolute URL to product page |
| store      | str         | Always "emag" |
| img_url    | str         | Product image URL |

---

## Environment Variables (`.env`)

| Variable        | Default | Description |
|-----------------|---------|-------------|
| DATABASE_URL    | postgresql://postgres:postgres@localhost:5432/emag_scraper | PostgreSQL connection string |
| HOST            | 0.0.0.0 | FastAPI host |
| PORT            | 8000    | FastAPI port |
| RELOAD          | True    | Enable auto‑reload |
| HEADLESS        | True    | Run Playwright in headless mode |
| USER_AGENT      | (see config.py) | Browser user‑agent |
| REQUEST_DELAY   | 2.0     | Seconds between requests to Emag |
| MAX_RETRIES     | 3        | Retry count on scrape failure |

---

## How the `pages` Property Works

- **Single job** (`POST /scrape`): the `pages` field sets how many search‑result pages are scraped for the keyword.  
  Example: `"pages": 3` will scrape page 1, page 2, and page 3 of the Emag search results.
- **Batch job** (`POST /scrape/batch`): the `pages` field applies to *each* keyword.  
  Example: `{"keywords":["nike","adidas"],"pages":2}` creates two jobs, each scraping 2 pages.
- **Background task**: the `_run_scrape_job` function loops from `page=1` to `page=pages` and calls `scrape_emag(..., page=p)` for each.
- **GET /scrape** (direct scrape) does **not** use the `pages` property; it only scrapes the single page given in the `page` query parameter.

---

## Running the API

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Start the server (development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Health Check

`GET /health` → `{"status": "ok"}`
