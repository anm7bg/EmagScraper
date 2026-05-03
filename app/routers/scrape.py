"""Router for triggering and monitoring scrape jobs."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..db.session import get_db, AsyncSessionLocal
from ..models.scrape_job import ScrapeJob, JobStatus, ScrapeRequest, ScrapeJobRead, ScrapeBatchRequest
from ..schemas import ScrapeResponse
from datetime import datetime
from ..scraper.emag import scrape_emag

router = APIRouter(prefix="/api/scrape", tags=["scrape"])

async def _run_scrape_job(job_id: int, keyword: str, store: str, pages: int = 1):
    """Background task that runs the scraper for N pages and updates the job."""
    async with AsyncSessionLocal() as db:
        job = await db.get(ScrapeJob, job_id)
        if not job:
            return
        job.status = JobStatus.RUNNING
        await db.commit()
        total_products = 0
        try:
            for p in range(1, pages + 1):
                products = await scrape_emag(keyword, store=store, page=p)
                total_products += len(products)
            job.products_found = total_products
            job.status = JobStatus.SUCCESS
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
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
        status=JobStatus.PENDING,
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
async def scrape_products(keyword: str, page: int = 1):
    """Scrape products for a keyword and return a list of product data.
    Example: GET /scrape?keyword=nike&page=1
    """
    products = await scrape_emag(keyword, store="emag.bg", page=page)
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
            status=JobStatus.PENDING,
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
