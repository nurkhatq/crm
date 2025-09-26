"""
Улучшенные Celery задачи для синхронизации с МойСклад
"""
import logging
from celery import Celery
from app.core.config import settings
from app.services.enhanced_sync import EnhancedSyncService, SyncSessionLocal

logger = logging.getLogger(__name__)

# Создаем Celery приложение
celery_app = Celery(
    "crm_enhanced_sync",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.enhanced_sync_tasks"]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,  # 25 минут
)


@celery_app.task(bind=True, name="enhanced_sync_products")
def enhanced_sync_products_task(self, force: bool = False):
    """Улучшенная синхронизация товаров"""
    try:
        logger.info(f"Starting enhanced products sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_products_enhanced(force=force)
            
        logger.info(f"Enhanced products sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced products sync task: {e}")
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_services")
def enhanced_sync_services_task(self, force: bool = False):
    """Синхронизация услуг"""
    try:
        logger.info(f"Starting services sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_services()
            
        logger.info(f"Services sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in services sync task: {e}")
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_bundles")
def enhanced_sync_bundles_task(self, force: bool = False):
    """Синхронизация комплектов"""
    try:
        logger.info(f"Starting bundles sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_bundles()
            
        logger.info(f"Bundles sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in bundles sync task: {e}")
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_stores")
def enhanced_sync_stores_task(self, force: bool = False):
    """Синхронизация складов"""
    try:
        logger.info(f"Starting stores sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_stores()
            
        logger.info(f"Stores sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in stores sync task: {e}")
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_sync_currencies")
def enhanced_sync_currencies_task(self, force: bool = False):
    """Синхронизация валют"""
    try:
        logger.info(f"Starting currencies sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.sync_currencies()
            
        logger.info(f"Currencies sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in currencies sync task: {e}")
        return {"error": str(e), "status": "error"}


@celery_app.task(bind=True, name="enhanced_full_sync")
def enhanced_full_sync_task(self, force: bool = False):
    """Полная улучшенная синхронизация всех данных"""
    try:
        logger.info(f"Starting enhanced full sync (force={force})")
        
        with SyncSessionLocal() as db:
            sync_service = EnhancedSyncService(db)
            result = sync_service.full_enhanced_sync(force=force)
            
        logger.info(f"Enhanced full sync completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in enhanced full sync task: {e}")
        return {"error": str(e), "status": "error"}
