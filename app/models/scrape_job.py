"""SQLAlchemy model and Pydantic schemas for scrape jobs."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from ..db.session import Base
from pydantic import BaseModel, Field


# ---------- SQLAlchemy model ----------

class JobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, nullable=False)
    store = Column(String, nullable=False)  # e.g., "emag.bg"
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
    products_found = Column(Integer, default=0, nullable=False)
    pages = Column(Integer, default=1, nullable=False)
    async_mode = Column(Boolean, default=True, nullable=False)


# ---------- Pydantic schemas ----------

class ScrapeJobBase(BaseModel):
    keyword: str
    store: str = Field(default="emag.bg", description="Only emag.bg is supported")
    pages: int = Field(default=1, description="Number of pages to scrape per keyword")

    class Config:
        orm_mode = True


class ScrapeJobCreate(ScrapeJobBase):
    pass


class ScrapeJobRead(ScrapeJobBase):
    id: int
    status: str
    created_at: datetime
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    products_found: int
    async_mode: bool


class ScrapeRequest(BaseModel):
    keyword: str
    store: str = Field(default="emag.bg", description="Only emag.bg is supported")
    pages: int = Field(default=1, description="Number of pages to scrape")
    async_mode: bool = Field(default=True, description="Run scrape in background")


class ScrapeBatchRequest(BaseModel):
    keywords: List[str] = Field(..., description="List of keywords to scrape")
    store: str = Field(default="emag.bg", description="Only emag.bg is supported")
    pages: int = Field(default=1, description="Number of pages to scrape per keyword")
    async_mode: bool = Field(default=True, description="Run scrape jobs in background")
