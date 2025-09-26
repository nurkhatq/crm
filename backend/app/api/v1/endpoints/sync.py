"""
Synchronization endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.sync import SyncRequest, SyncResponse, SyncLog
from app.services.sync import SyncService
from app.tasks.sync_tasks import (
    sync_products_task, sync_customers_task, sync_documents_task, sync_stock_task, sync_stores_task, full_sync_task,
    enhanced_sync_products_task, enhanced_sync_services_task, enhanced_sync_bundles_task,
    enhanced_sync_stores_task, enhanced_sync_currencies_task, enhanced_full_sync_task,
    enhanced_sync_turnover_task, enhanced_sync_retail_documents_task, enhanced_sync_employee_context_task
)

router = APIRouter()


@router.post("/sync", response_model=SyncResponse)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger synchronization with MoySklad"""
    
    sync_service = SyncService(db)
    
    try:
        if request.sync_type == "full":
            # Trigger full sync in background
            task = full_sync_task.delay(force=request.force)
            return SyncResponse(
                message="Full synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "products":
            task = sync_products_task.delay(force=request.force)
            return SyncResponse(
                message="Products synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "customers":
            task = sync_customers_task.delay(force=request.force)
            return SyncResponse(
                message="Customers synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "documents":
            task = sync_documents_task.delay(force=request.force)
            return SyncResponse(
                message="Documents synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "stock":
            task = sync_stock_task.delay(force=request.force)
            return SyncResponse(
                message="Stock synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "stores":
            task = sync_stores_task.delay(force=request.force)
            return SyncResponse(
                message="Stores synchronization started",
                sync_id=None,
                status="started"
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid sync type. Must be one of: full, products, customers, documents, stock, stores"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start synchronization: {str(e)}")


@router.get("/status", response_model=list[SyncLog])
async def get_sync_status(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Get recent synchronization status"""
    
    from sqlalchemy import select, desc
    from app.models import SyncLog as SyncLogModel
    
    query = select(SyncLogModel).order_by(desc(SyncLogModel.started_at)).limit(limit)
    result = await db.execute(query)
    sync_logs = result.scalars().all()
    
    return sync_logs


@router.get("/test-connection")
async def test_moysklad_connection():
    """Test connection to MoySklad API"""
    from app.connectors.moysklad import MoySkladConnector
    
    connector = MoySkladConnector()
    
    if not connector.is_enabled():
        return {"status": "error", "message": "MoySklad connector is not enabled"}
    
    try:
        # Test basic connection
        success = await connector.test_connection()
        
        if success:
            return {
                "status": "success", 
                "message": "Connection to MoySklad API successful",
                "token_configured": True
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to connect to MoySklad API",
                "token_configured": True
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Connection test failed: {str(e)}",
            "token_configured": connector.is_enabled()
        }


@router.post("/sync/enhanced", response_model=SyncResponse)
async def trigger_enhanced_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Trigger enhanced synchronization with MoySklad (полное извлечение данных)"""
    
    try:
        if request.sync_type == "full":
            # Запускаем полную улучшенную синхронизацию
            task = enhanced_full_sync_task.delay(force=request.force)
            return SyncResponse(
                message="Enhanced full synchronization started (все доступные данные)",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "products":
            task = enhanced_sync_products_task.delay(force=request.force)
            return SyncResponse(
                message="Enhanced products synchronization started (с расширенными данными)",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "services":
            task = enhanced_sync_services_task.delay(force=request.force)
            return SyncResponse(
                message="Services synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "bundles":
            task = enhanced_sync_bundles_task.delay(force=request.force)
            return SyncResponse(
                message="Bundles synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "stores":
            task = enhanced_sync_stores_task.delay(force=request.force)
            return SyncResponse(
                message="Enhanced stores synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "currencies":
            task = enhanced_sync_currencies_task.delay(force=request.force)
            return SyncResponse(
                message="Currencies synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "turnover":
            task = enhanced_sync_turnover_task.delay(force=request.force)
            return SyncResponse(
                message="Turnover reports synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "retail_documents":
            task = enhanced_sync_retail_documents_task.delay(force=request.force)
            return SyncResponse(
                message="Retail documents synchronization started",
                sync_id=None,
                status="started"
            )
        
        elif request.sync_type == "employee_context":
            task = enhanced_sync_employee_context_task.delay(force=request.force)
            return SyncResponse(
                message="Employee context synchronization started",
                sync_id=None,
                status="started"
            )
        
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid enhanced sync type. Must be one of: full, products, services, bundles, stores, currencies, turnover, retail_documents, employee_context"
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enhanced synchronization: {str(e)}")


@router.get("/api-analysis")
async def get_api_analysis():
    """Получить анализ доступных API endpoints МойСклад"""
    try:
        # Возвращаем результаты анализа API
        analysis_results = {
            "available_endpoints": {
                "products": {"count": 103, "description": "Товары"},
                "assortment": {"count": 152, "description": "Весь ассортимент (товары + услуги + комплекты)"},
                "services": {"count": 1, "description": "Услуги"},
                "bundles": {"count": 48, "description": "Комплекты"},
                "stock_all": {"count": 46, "description": "Остатки всех товаров"},
                "stock_bystore": {"count": 46, "description": "Остатки по складам"},
                "counterparties": {"count": 6, "description": "Контрагенты"},
                "organizations": {"count": 1, "description": "Организации"},
                "demands": {"count": 51, "description": "Отгрузки"},
                "salesreturns": {"count": 28, "description": "Возвраты покупателей"},
                "supplies": {"count": 40, "description": "Приемки"},
                "stores": {"count": 6, "description": "Склады"},
                "moves": {"count": 2, "description": "Перемещения"},
                "currencies": {"count": 1, "description": "Валюты"},
                "uom": {"count": 62, "description": "Единицы измерения"},
                "productfolders": {"count": 15, "description": "Группы товаров"},
                "contracts": {"count": 1, "description": "Договоры"},
                "countries": {"count": 252, "description": "Страны"},
                "profit_byproduct": {"count": 34, "description": "Прибыльность по товарам"},
                "employee_context": {"count": 1, "description": "Контекст сотрудника"},
                "turnover_reports": {"count": "unknown", "description": "Отчеты по оборотам товаров"},
                "retail_documents": {"count": "unknown", "description": "Розничные документы"}
            },
            "unavailable_endpoints": [
                "customerorders", "invoiceouts", "purchaseorders", "invoiceins", 
                "purchasereturns", "enters", "losses", "inventories", "projects"
            ],
            "api_errors": [
                "retailsale", "pricetype", "money_cash", "stock_all_current"
            ],
            "recommendations": [
                "Использовать enhanced sync для получения максимального объема данных",
                "Синхронизировать все доступные типы товаров (products, services, bundles)",
                "Получать остатки из нескольких endpoints для полноты данных",
                "Синхронизировать справочники (stores, currencies, uom, countries)"
            ]
        }
        
        return analysis_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API analysis: {str(e)}")