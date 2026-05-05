from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock
from app.main import app
from app.scraper import emag

# Mock the async scraper to avoid DB and network calls during tests
@pytest.fixture(autouse=True)
def mock_scrape(monkeypatch):
    dummy_product = {
        "title": "Test Phone",
        "price": 123.45,
        "raw_price": "123.45 BGN",
        "url": "http://example.com/product",
        "store": "emag",
        "img_url": "http://example.com/image.png",
        "categories": ["Category1", "Category2"],
    }
    async_mock = AsyncMock(return_value=[dummy_product])
    monkeypatch.setattr(emag, "scrape_emag", async_mock)

# Override DB dependency with a dummy async session
from app.db.session import get_db

class DummyAsyncSession:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def add(self, *args, **kwargs):
        pass
    async def commit(self):
        pass
    async def refresh(self, *args, **kwargs):
        pass
    async def execute(self, *args, **kwargs):
        class Result:
            def scalar_one_or_none(self):
                return None
        return Result()
    async def scalar_one_or_none(self):
        return None

# Apply override
app.dependency_overrides[get_db] = lambda: DummyAsyncSession()

client = TestClient(app)


def test_scrape_endpoint_status():
    """Simulate Next.js GET request to /api/scrape/ and check status."""
    response = client.get("/api/scrape/", params={"keyword": "iphone", "page": 1})
    assert response.status_code == 200


def test_scrape_endpoint_structure():
    response = client.get("/api/scrape/", params={"keyword": "iphone", "page": 1})
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)


def test_scrape_endpoint_product_fields():
    response = client.get("/api/scrape/", params={"keyword": "iphone", "page": 1})
    assert response.status_code == 200
    data = response.json()
    if len(data["products"]) > 0:
        product = data["products"][0]
        for key in ("title", "price", "url", "store", "img_url"):
            assert key in product, f"Missing key: {key}"


def test_scrape_endpoint_invalid_store_not_applicable():
    # The API always uses emag.bg, so no invalid store test needed via endpoint
    pass


def test_scrape_endpoint_empty_keyword():
    response = client.get("/api/scrape/", params={"keyword": "", "page": 1})
    # Should still return 200 (scraper may return empty list)
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
