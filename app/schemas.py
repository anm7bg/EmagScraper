."""Pydantic response schemas for the scraping API."""

from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ProductOut(BaseModel):
    title: str = Field(..., description="Product title")
    categories: List[str] = Field(default_factory=list, description="Category hierarchy (optional)")
    price: float = Field(..., description="Numeric price in EUR")
    raw_price: str = Field(..., description="Original price string from the site")
    url: str = Field(..., description="Absolute URL to the product page")
    store: str = Field(..., description="Store identifier, e.g. 'emag'")
    img_url: str = Field(..., description="URL to the product image")

    class Config:
        orm_mode = True


class ScrapeResponse(BaseModel):
    products: List[ProductOut] = Field(default_factory=list, description="List of scraped products")

    class Config:
        orm_mode = True
