"""SQLAlchemy models and Pydantic schemas for products and price history."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship

from ..db.session import Base
from pydantic import BaseModel, Field

# ---------- SQLAlchemy models ----------

class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("external_id", "store", name="uq_product_external_store"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(nullable=False)  # ID from Emag site
    store: Mapped[str] = mapped_column(nullable=False)  # e.g., "emag.bg" or "emag.ro"
    title: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(nullable=False, default="EUR")
    image_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    product_url: Mapped[str] = mapped_column(nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    categories: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True, default=list)

    # Relationship to price history
    price_history: Mapped[List["PriceHistory"]] = relationship(
        "PriceHistory", back_populates="product", cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = "price_history"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    raw_price: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="price_history")


# ---------- Pydantic schemas ----------

class ProductBase(BaseModel):
    external_id: str = Field(..., description="External Emag product identifier")
    store: str = Field(..., description="Store domain, e.g., emag.bg")
    title: str
    price: float
    currency: str = "EUR"
    image_url: Optional[str] = None
    product_url: str

    class Config:
        orm_mode = True


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    scraped_at: datetime
    categories: List[str] = []
    price_history: List["PriceHistoryRead"] = []

class PriceHistoryBase(BaseModel):
    price: float
    raw_price: str

    class Config:
        orm_mode = True


class PriceHistoryCreate(PriceHistoryBase):
    pass


class PriceHistoryRead(PriceHistoryBase):
    id: int
    created_at: datetime

# Resolve forward references
ProductRead.update_forward_refs()
PriceHistoryRead.update_forward_refs()
