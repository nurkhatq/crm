"""
Обновленные endpoints для синхронизации с улучшенной обработкой ошибок
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel

from app.core.database import get_db
from app.services.sync import SyncService
from app.models import SyncLog
from app.connectors.moysklad import moysklad_connector

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncRequest(BaseModel):
    sync_type: str = "full"  # full, products, customers, documents, stock, stores
    force: bool = False


class SyncResponse(BaseModel):
    status: str
    message: str
    sync_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class SyncStatusResponse(BaseModel):
    id: int
    sync_type: str
    entity_type: str
    status: str
    started_at: str
    completed_at: Optional[str]
    records_processed: int
    records_created: int
    records_updated: int
    records_errors: int
    error_details: Optional[str]


@router.post("/sync", response_model=SyncResponse)
async def start_sync(
    sync_request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Запустить синхронизацию данных из МойСклад
    
    Типы синхронизации:
    - full: Полная синхронизация всех данных
    - products: Только товары
    - customers: Только контрагенты
    - stores: Только склады
    - stock: Только остатки товаров
    """
    
    # Проверяем, включен ли коннектор
    if not moysklad_connector.is_enabled():
        logger.warning("🚫 Попытка синхронизации при отключенном коннекторе")
        raise HTTPException(
            status_code=400,
            detail="MoySklad connector is not enabled. Please check your token configuration."
        )
    
    # Проверяем соединение
    try:
        connection_ok = await moysklad_connector.test_connection()
        if not connection_ok:
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to MoySklad API. Please check your token and network connection."
            )
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования соединения: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection test failed: {str(e)}"
        )
    
    # Валидация типа синхронизации
    valid_sync_types = ["full", "products", "customers", "stores", "stock"]
    if sync_request.sync_type not in valid_sync_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sync_type. Must be one of: {', '.join(valid_sync_types)}"
        )
    
    try:
        sync_service = SyncService(db)
        
        logger.info(f"🚀 Запуск синхронизации: {sync_request.sync_type} (force: {sync_request.force})")
        
        # Выбираем метод синхронизации
        if sync_request.sync_type == "full":
            background_tasks.add_task(
                run_full_sync, 
                sync_service, 
                sync_request.force
            )
            message = "Full synchronization started in background"
            
        elif sync_request.sync_type == "products":
            background_tasks.add_task(
                run_products_sync, 
                sync_service, 
                sync_request.force
            )
            message = "Products synchronization started in background"
            
        elif sync_request.sync_type == "customers":
            background_tasks.add_task(
                run_customers_sync, 
                sync_service, 
                sync_request.force
            )
            message = "Customers synchronization started in background"
            
        elif sync_request.sync_type == "stores":
            background_tasks.add_task(
                run_stores_sync, 
                sync_service
            )
            message = "Stores synchronization started in background"
            
        elif sync_request.sync_type == "stock":
            background_tasks.add_task(
                run_stock_sync, 
                sync_service
            )
            message = "Stock synchronization started in background"
        
        logger.info(f"✅ Синхронизация {sync_request.sync_type} запущена в фоне")
        
        return SyncResponse(
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска синхронизации: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start synchronization: {str(e)}"
        )


# Background task функции
async def run_full_sync(sync_service: SyncService, force: bool):
    """Запуск полной синхронизации в фоне"""
    try:
        result = await sync_service.full_sync(force)
        logger.info(f"✅ Полная синхронизация завершена: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка полной синхронизации: {e}")


async def run_products_sync(sync_service: SyncService, force: bool):
    """Запуск синхронизации товаров в фоне"""
    try:
        result = await sync_service.sync_products(force)
        logger.info(f"✅ Синхронизация товаров завершена: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации товаров: {e}")


async def run_customers_sync(sync_service: SyncService, force: bool):
    """Запуск синхронизации контрагентов в фоне"""
    try:
        result = await sync_service.sync_customers(force)
        logger.info(f"✅ Синхронизация контрагентов завершена: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации контрагентов: {e}")


async def run_stores_sync(sync_service: SyncService):
    """Запуск синхронизации складов в фоне"""
    try:
        result = await sync_service.sync_stores()
        logger.info(f"✅ Синхронизация складов завершена: {result}")
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации складов: {e}")


async def run_stock_sync(sync_service: SyncService):
    """Запуск синхронизации остатков в фоне"""
    try:
        # Получаем отчет об остатках
        stock_data = await moysklad_connector.get_stock_report()
        logger.info(f"✅ Получен отчет об остатках: {len(stock_data)} записей")
        
        # TODO: Сохранить остатки в БД
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации остатков: {e}")


@router.get("/status", response_model=list[SyncStatusResponse])
async def get_sync_status(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Получить статус последних синхронизаций"""
    try:
        query = select(SyncLog).order_by(desc(SyncLog.started_at)).limit(limit)
        result = await db.execute(query)
        sync_logs = result.scalars().all()
        
        response_logs = []
        for log in sync_logs:
            response_logs.append(SyncStatusResponse(
                id=log.id,
                sync_type=log.sync_type,
                entity_type=log.entity_type,
                status=log.status,
                started_at=log.started_at.isoformat(),
                completed_at=log.completed_at.isoformat() if log.completed_at else None,
                records_processed=log.records_processed,
                records_created=log.records_created,
                records_updated=log.records_updated,
                records_errors=log.records_errors,
                error_details=log.error_details
            ))
        
        return response_logs
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса синхронизации: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.get("/test-connection")
async def test_moysklad_connection():
    """Тестировать соединение с API МойСклад"""
    try:
        if not moysklad_connector.is_enabled():
            return {
                "status": "disabled",
                "message": "MoySklad connector is not enabled. Please configure MOYSKLAD_TOKEN in .env file.",
                "token_configured": False
            }
        
        # Тестируем соединение
        connection_ok = await moysklad_connector.test_connection()
        
        if connection_ok:
            return {
                "status": "success",
                "message": "✅ Connection to MoySklad API successful",
                "token_configured": True
            }
        else:
            return {
                "status": "error",
                "message": "❌ Failed to connect to MoySklad API. Please check your token.",
                "token_configured": True
            }
            
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования соединения: {e}")
        return {
            "status": "error",
            "message": f"❌ Connection test failed: {str(e)}",
            "token_configured": moysklad_connector.is_enabled()
        }


@router.get("/api-status")
async def get_api_status():
    """Получить расширенную информацию о статусе API"""
    try:
        if not moysklad_connector.is_enabled():
            return {
                "connector_enabled": False,
                "token_configured": False,
                "api_accessible": False,
                "message": "Connector is disabled - no token configured"
            }
        
        # Тестируем различные endpoints
        endpoints_status = {}
        
        # Тестируем товары
        try:
            products_data, status_code = await moysklad_connector._make_request(
                'GET', 'entity/product', params={'limit': 1}
            )
            endpoints_status['products'] = {
                'accessible': status_code == 200,
                'count': products_data.get('meta', {}).get('size', 0) if status_code == 200 else 0
            }
        except Exception as e:
            endpoints_status['products'] = {'accessible': False, 'error': str(e)}
        
        # Тестируем контрагентов
        try:
            customers_data, status_code = await moysklad_connector._make_request(
                'GET', 'entity/counterparty', params={'limit': 1}
            )
            endpoints_status['customers'] = {
                'accessible': status_code == 200,
                'count': customers_data.get('meta', {}).get('size', 0) if status_code == 200 else 0
            }
        except Exception as e:
            endpoints_status['customers'] = {'accessible': False, 'error': str(e)}
        
        # Тестируем склады
        try:
            stores_data, status_code = await moysklad_connector._make_request(
                'GET', 'entity/store', params={'limit': 1}
            )
            endpoints_status['stores'] = {
                'accessible': status_code == 200,
                'count': stores_data.get('meta', {}).get('size', 0) if status_code == 200 else 0
            }
        except Exception as e:
            endpoints_status['stores'] = {'accessible': False, 'error': str(e)}
        
        return {
            "connector_enabled": True,
            "token_configured": True,
            "api_accessible": any(ep.get('accessible', False) for ep in endpoints_status.values()),
            "endpoints": endpoints_status,
            "message": "API status check completed"
        }
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса API: {e}")
        return {
            "connector_enabled": moysklad_connector.is_enabled(),
            "token_configured": moysklad_connector.is_enabled(),
            "api_accessible": False,
            "error": str(e),
            "message": "Failed to check API status"
        }