"""
Tests for API endpoints
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "crm-backend"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_products_endpoint(client: AsyncClient):
    """Test products endpoint"""
    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_customers_endpoint(client: AsyncClient):
    """Test customers endpoint"""
    response = await client.get("/api/v1/customers/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_documents_endpoint(client: AsyncClient):
    """Test documents endpoint"""
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_analytics_kpi_endpoint(client: AsyncClient):
    """Test analytics KPI endpoint"""
    response = await client.get("/api/v1/analytics/kpi")
    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data
    assert "total_customers" in data
    assert "total_documents" in data
    assert "total_revenue" in data
    assert "total_stock_value" in data
    assert "low_stock_products" in data


@pytest.mark.asyncio
async def test_sync_endpoint(client: AsyncClient):
    """Test sync endpoint"""
    response = await client.post(
        "/api/v1/connectors/moysklad/sync",
        json={"sync_type": "products", "force": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_products_search(client: AsyncClient):
    """Test products search functionality"""
    response = await client.get("/api/v1/products/?search=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_products_pagination(client: AsyncClient):
    """Test products pagination"""
    response = await client.get("/api/v1/products/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 10
