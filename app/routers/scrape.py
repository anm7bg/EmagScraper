"""Router for triggering and monitoring scrape jobs."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
import asyncio
import logging
from ..config import settings
logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..db.session import get_db, AsyncSessionLocal
from ..models.scrape_job import ScrapeJob, JobStatus, ScrapeRequest, ScrapeJobRead, ScrapeBatchRequest
from ..schemas import ScrapeResponse
from datetime import datetime
from ..scraper.emag import scrape_emag
from sqlalchemy import select
from ..models.product import Product, PriceHistory

router = APIRouter(prefix="/api/scrape", tags=["scrape"])

async def _run_scrape_job(job_id: int, keyword: str, store: str, pages: int = 1):
    """Background task that runs the scraper for N pages and updates the job."""
    import re
    async with AsyncSessionLocal() as db:
        job = await db.get(ScrapeJob, job_id)
        if not job:
            return
        job.status = JobStatus.running
        await db.commit()
        logger.info(f"Scrape job {job_id} started for keyword '{keyword}' with {pages} page(s)")
        total_products = 0
        try:
            for p in range(1, pages + 1):
                logger.debug(f"Scraping page {p}/{pages} for job {job_id}")
                products = await scrape_emag(keyword, store=store, page=p)
                total_products += len(products)
                logger.debug(f"Found {len(products)} products on page {p}")
                for prod in products:
                    product_url = prod.get("url") or prod.get("product_url")
                    if not product_url:
                        continue
                    match = re.search(r'/pd/([^/?#]+)', product_url)
                    if not match:
                        continue
                    external_id = match.group(1)
                    stmt = select(Product).where(Product.external_id == external_id, Product.store == store).limit(1)
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    if existing:
                        existing.title = prod["title"]
                        existing.price = prod["price"]
                        existing.currency = prod.get("currency", "EUR")
                        existing.image_url = prod.get("img_url") or prod.get("image_url")
                        existing.product_url = product_url
                        existing.categories = prod.get("categories", [])
                        product_obj = existing
                    else:
                        product_obj = Product(
                            external_id=external_id,
                            store=store,
                            title=prod["title"],
                            price=prod["price"],
                            currency=prod.get("currency", "EUR"),
                            image_url=prod.get("img_url") or prod.get("image_url"),
                            product_url=product_url,
                            categories=prod.get("categories", []),
                        )
                        db.add(product_obj)
                    price_hist = PriceHistory(
                        product=product_obj,
                        price=prod["price"],
                        raw_price=prod.get("raw_price", str(prod["price"])),
                    )
                    db.add(price_hist)
                await db.commit()
                # Respect request delay between pages
                if p < pages:
                    await asyncio.sleep(settings.request_delay)
            job.products_found = total_products
            job.status = JobStatus.success
            logger.info(f"Scrape job {job_id} completed successfully, {total_products} products stored")
        except Exception as e:
            job.status = JobStatus.failed
            job.error = str(e)
            logger.exception(f"Scrape job {job_id} failed: {e}")
        finally:
            job.finished_at = datetime.utcnow()
            await db.commit()


@router.post("/", response_model=ScrapeJobRead, status_code=202)
async def start_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start a new scrape job for the given keyword and store."""
    # Restrict to emag.bg only
    job = ScrapeJob(
        keyword=request.keyword,
        store="emag.bg",
        pages=request.pages,
        status=JobStatus.pending,
        created_at=datetime.utcnow(),
        async_mode=request.async_mode,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    if request.async_mode:
        background_tasks.add_task(_run_scrape_job, job.id, request.keyword, "emag.bg", request.pages)
    else:
        # Synchronous execution (blocking)
        await _run_scrape_job(job.id, request.keyword, "emag.bg", request.pages)

    return job


@router.get("/{job_id}", response_model=ScrapeJobRead)
async def get_scrape_status(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await db.get(ScrapeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return job


@router.get("/", response_model=ScrapeResponse)
async def scrape_products(keyword: str, page: int = 1, db: AsyncSession = Depends(get_db)):
    """Scrape products for a keyword and return a list of product data.
    Example: GET /scrape?keyword=nike&page=1
    """
    import re
    products = await scrape_emag(keyword, store="emag.bg", page=page)
    # Persist products to database
    for prod in products:
        product_url = prod.get("url") or prod.get("product_url")
        if not product_url:
            continue
        match = re.search(r'/pd/([^/?#]+)', product_url)
        if not match:
            continue
        external_id = match.group(1)
        stmt = select(Product).where(Product.external_id == external_id, Product.store == "emag.bg").limit(1)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.title = prod["title"]
            existing.price = prod["price"]
            existing.currency = prod.get("currency", "EUR")
            existing.image_url = prod.get("img_url") or prod.get("image_url")
            existing.product_url = product_url
            existing.categories = prod.get("categories", [])
            product_obj = existing
        else:
            product_obj = Product(
                external_id=external_id,
                store="emag.bg",
                title=prod["title"],
                price=prod["price"],
                currency=prod.get("currency", "EUR"),
                image_url=prod.get("img_url") or prod.get("image_url"),
                product_url=product_url,
                categories=prod.get("categories", []),
            )
            db.add(product_obj)
        price_hist = PriceHistory(
            product=product_obj,
            price=prod["price"],
            raw_price=prod.get("raw_price", str(prod["price"])),
        )
        db.add(price_hist)
    await db.commit()
    return ScrapeResponse(products=products)


@router.post("/scrape/batch", response_model=List[ScrapeJobRead], status_code=202)
async def batch_scrape(
    request: ScrapeBatchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple scrape jobs for a list of keywords (for cron/automation)."""
    jobs = []
    for keyword in request.keywords:
        job = ScrapeJob(
            keyword=keyword,
            store="emag.bg",
            pages=request.pages,
            status=JobStatus.pending,
            created_at=datetime.utcnow(),
            async_mode=request.async_mode,
        )
        db.add(job)
        jobs.append(job)
    await db.commit()
    for job in jobs:
        await db.refresh(job)
        if request.async_mode:
            background_tasks.add_task(
                _run_scrape_job, job.id, job.keyword, "emag.bg", request.pages
            )
        else:
            await _run_scrape_job(job.id, job.keyword, "emag.bg", request.pages)
    return jobs
