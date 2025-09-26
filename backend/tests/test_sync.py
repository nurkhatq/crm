"""
Tests for synchronization service
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.sync import SyncService
from app.models import Product, Customer, Document, SyncLog


@pytest.mark.asyncio
async def test_sync_products_disabled_connector(db_session):
    """Test sync products when connector is disabled"""
    with patch('app.connectors.moysklad.moysklad_connector.is_enabled', return_value=False):
        sync_service = SyncService(db_session)
        result = await sync_service.sync_products()
        
        assert "error" in result
        assert result["error"] == "MoySklad connector is not enabled"


@pytest.mark.asyncio
async def test_sync_products_success(db_session):
    """Test successful products sync"""
    # Mock connector
    mock_products_data = [
        {
            "id": "test-product-1",
            "name": "Test Product 1",
            "code": "TP001",
            "article": "ART001",
            "description": "Test description",
            "archived": False,
            "updated": "2024-01-01T00:00:00Z",
            "salePrices": [{"value": 100.0}],
            "buyPrice": {"value": 80.0},
            "uom": {"name": "шт"},
            "productFolder": {"name": "Test Group"},
            "supplier": {"name": "Test Supplier"}
        }
    ]
    
    with patch('app.connectors.moysklad.moysklad_connector.is_enabled', return_value=True), \
         patch('app.connectors.moysklad.moysklad_connector.get_all_products', return_value=mock_products_data):
        
        sync_service = SyncService(db_session)
        result = await sync_service.sync_products()
        
        assert result["status"] == "success"
        assert result["records_processed"] == 1
        assert result["records_created"] == 1
        assert result["records_updated"] == 0
        assert result["records_errors"] == 0
        
        # Check that product was created
        products = await db_session.execute("SELECT * FROM products")
        products = products.fetchall()
        assert len(products) == 1


@pytest.mark.asyncio
async def test_sync_customers_success(db_session):
    """Test successful customers sync"""
    # Mock connector
    mock_customers_data = [
        {
            "id": "test-customer-1",
            "name": "Test Customer 1",
            "code": "TC001",
            "legalTitle": "Test Customer LLC",
            "email": "test@example.com",
            "phone": "+1234567890",
            "inn": "1234567890",
            "kpp": "123456789",
            "archived": False,
            "updated": "2024-01-01T00:00:00Z",
            "actualAddress": {
                "city": "Test City",
                "street": "Test Street",
                "house": "1"
            }
        }
    ]
    
    with patch('app.connectors.moysklad.moysklad_connector.is_enabled', return_value=True), \
         patch('app.connectors.moysklad.moysklad_connector.get_all_customers', return_value=mock_customers_data):
        
        sync_service = SyncService(db_session)
        result = await sync_service.sync_customers()
        
        assert result["status"] == "success"
        assert result["records_processed"] == 1
        assert result["records_created"] == 1
        assert result["records_updated"] == 0
        assert result["records_errors"] == 0


@pytest.mark.asyncio
async def test_sync_log_creation(db_session):
    """Test sync log creation and update"""
    sync_service = SyncService(db_session)
    
    # Create sync log
    sync_log = await sync_service.create_sync_log("test", "product")
    assert sync_log.sync_type == "test"
    assert sync_log.entity_type == "product"
    assert sync_log.status == "in_progress"
    
    # Update sync log
    await sync_service.update_sync_log(
        sync_log, 
        "success", 
        records_processed=10,
        records_created=5,
        records_updated=3,
        records_errors=2
    )
    
    assert sync_log.status == "success"
    assert sync_log.records_processed == 10
    assert sync_log.records_created == 5
    assert sync_log.records_updated == 3
    assert sync_log.records_errors == 2
    assert sync_log.completed_at is not None
