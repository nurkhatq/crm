"""
Celery tasks for synchronization
"""
import asyncio
from celery import current_task
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.sync import SyncService
from app.services.enhanced_sync import EnhancedSyncService, SyncSessionLocal
from app.tasks.celery_app import celery_app

# Create async engine for tasks
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    future=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db_session() -> AsyncSession:
    """Get database session for tasks"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@celery_app.task(bind=True)
def sync_products_task(self, force: bool = False):
    """Sync products from MoySklad"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.sync_products(force=force)
        return result


@celery_app.task(bind=True)
def sync_customers_task(self, force: bool = False):
    """Sync customers from MoySklad"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.sync_customers(force=force)
        return result


@celery_app.task(bind=True)
def sync_documents_task(self, force: bool = False):
    """Sync documents from MoySklad"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.sync_documents(force=force)
        return result


@celery_app.task(bind=True)
def sync_stock_task(self, force: bool = False):
    """Sync stock from MoySklad"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.sync_stock(force=force)
        return result


@celery_app.task(bind=True)
def sync_stores_task(self, force: bool = False):
    """Sync stores from MoySklad"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.sync_stores(force=force)
        return result


@celery_app.task(bind=True)
def full_sync_task(self, force: bool = False):
    """Perform full synchronization"""
    from app.services.sync_sync import SyncSyncService
    from app.services.sync_sync import SyncSessionLocal
    
    with SyncSessionLocal() as db:
        sync_service = SyncSyncService(db)
        result = sync_service.full_sync(force=force)
        return result


# Enhanced sync tasks
@celery_app.task(bind=True, name="enhanced_sync_products")
def enhanced_sync_products_task(self, force: bool = False):
    """Enhanced products sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_products_enhanced(force=force)
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_services")
def enhanced_sync_services_task(self, force: bool = False):
    """Services sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_services()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_bundles")
def enhanced_sync_bundles_task(self, force: bool = False):
    """Bundles sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_bundles()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_stores")
def enhanced_sync_stores_task(self, force: bool = False):
    """Stores sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_stores()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_currencies")
def enhanced_sync_currencies_task(self, force: bool = False):
    """Currencies sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_currencies()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_full_sync")
def enhanced_full_sync_task(self, force: bool = False):
    """Enhanced full sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.full_enhanced_sync(force=force)
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_turnover")
def enhanced_sync_turnover_task(self, force: bool = False):
    """Turnover reports sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_turnover_reports()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_retail_documents")
def enhanced_sync_retail_documents_task(self, force: bool = False):
    """Retail documents sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_retail_documents()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_employee_context")
def enhanced_sync_employee_context_task(self, force: bool = False):
    """Employee context sync task"""
    try:
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_employee_context()
        return result
    except Exception as e:
        return {"error": str(e), "status": "error"}
