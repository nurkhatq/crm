"""
Улучшенный сервис синхронизации с МойСклад
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from app.connectors.moysklad import moysklad_connector
from app.models import Product, Customer, Document, SyncLog, Store
from app.core.database import get_db

logger = logging.getLogger(__name__)


class SyncService:
    """Улучшенный сервис синхронизации данных из МойСклад"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.connector = moysklad_connector
    
    async def create_sync_log(self, sync_type: str, entity_type: str) -> SyncLog:
        """Создать лог синхронизации"""
        sync_log = SyncLog(
            sync_type=sync_type,
            entity_type=entity_type,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            records_processed=0,
            records_created=0,
            records_updated=0,
            records_errors=0
        )
        
        self.db.add(sync_log)
        await self.db.commit()
        await self.db.refresh(sync_log)
        
        return sync_log
    
    async def update_sync_log(
        self, 
        sync_log: SyncLog, 
        status: str,
        records_processed: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        records_errors: int = 0,
        error_details: Optional[str] = None
    ):
        """Обновить лог синхронизации"""
        sync_log.status = status
        sync_log.completed_at = datetime.now(timezone.utc)
        sync_log.records_processed = records_processed
        sync_log.records_created = records_created
        sync_log.records_updated = records_updated
        sync_log.records_errors = records_errors
        
        if error_details:
            sync_log.error_details = error_details
        
        await self.db.commit()
    
    def _safe_get_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """Безопасное извлечение значения из вложенного словаря"""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            
            return current if current is not None else default
        except Exception:
            return default
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Парсинг даты из строки МойСклад"""
        if not date_str:
            return None
        
        try:
            # МойСклад возвращает даты в формате ISO 8601
            if date_str.endswith('Z'):
                date_str = date_str[:-1] + '+00:00'
            elif '+' not in date_str and not date_str.endswith('+00:00'):
                date_str = date_str + '+00:00'
            
            return datetime.fromisoformat(date_str)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось парсить дату '{date_str}': {e}")
            return None
    
    def _extract_price(self, price_data: Any, default: float = 0.0) -> float:
        """Извлечение цены из данных МойСклад"""
        if isinstance(price_data, dict):
            value = price_data.get('value', 0)
        elif isinstance(price_data, (int, float)):
            value = price_data
        elif isinstance(price_data, list) and price_data:
            # Берем первую цену из массива
            first_price = price_data[0]
            if isinstance(first_price, dict):
                value = first_price.get('value', default)
            else:
                value = default
        else:
            value = default
        
        try:
            # МойСклад хранит цены в копейках
            return float(value) / 100.0 if value else default
        except (ValueError, TypeError):
            return default
    
    async def sync_products(self, force: bool = False) -> Dict[str, Any]:
        """Синхронизация товаров"""
        if not self.connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("products", "product")
        
        try:
            logger.info("🔄 Начинаем синхронизацию товаров...")
            
            # Получаем все товары из МойСклад
            moysklad_products = await self.connector.get_all_products()
            
            if not moysklad_products:
                logger.warning("⚠️ Не получено товаров из МойСклад")
                await self.update_sync_log(sync_log, "completed", 0, 0, 0, 0)
                return {
                    "status": "completed",
                    "message": "No products found in MoySklad",
                    "records_processed": 0,
                    "records_created": 0,
                    "records_updated": 0,
                    "records_errors": 0
                }
            
            created_count = 0
            updated_count = 0
            error_count = 0
            processed_count = 0
            
            for product_data in moysklad_products:
                try:
                    processed_count += 1
                    product_id = product_data.get('id')
                    
                    if not product_id:
                        logger.warning(f"⚠️ Товар без ID пропущен: {product_data.get('name', 'Unknown')}")
                        error_count += 1
                        continue
                    
                    # Проверяем, существует ли товар
                    query = select(Product).where(Product.moysklad_id == product_id)
                    result = await self.db.execute(query)
                    existing_product = result.scalar_one_or_none()
                    
                    # Подготавливаем данные товара
                    product_dict = {
                        'moysklad_id': product_id,
                        'name': product_data.get('name', ''),
                        'code': product_data.get('code', ''),
                        'article': product_data.get('article', ''),
                        'description': product_data.get('description', ''),
                        'archived': product_data.get('archived', False),
                        'entity_type': product_data.get('entity_type', 'product'),
                        
                        # Цены
                        'sale_price': self._extract_price(
                            self._safe_get_value(product_data, 'salePrices', [])
                        ),
                        'buy_price': self._extract_price(
                            self._safe_get_value(product_data, 'buyPrice', {})
                        ),
                        
                        # Связанные сущности
                        'uom_name': self._safe_get_value(product_data, 'uom.name', ''),
                        'group_name': self._safe_get_value(product_data, 'productFolder.name', ''),
                        'supplier_name': self._safe_get_value(product_data, 'supplier.name', ''),
                        
                        # Метаданные
                        'updated_at': self._parse_datetime(
                            product_data.get('updated', '')
                        ) or datetime.now(timezone.utc),
                        'synced_at': datetime.now(timezone.utc)
                    }
                    
                    if existing_product:
                        # Обновляем существующий товар
                        for key, value in product_dict.items():
                            if hasattr(existing_product, key):
                                setattr(existing_product, key, value)
                        
                        updated_count += 1
                        if updated_count % 100 == 0:
                            logger.info(f"📊 Обновлено товаров: {updated_count}")
                    else:
                        # Создаем новый товар
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        created_count += 1
                        
                        if created_count % 100 == 0:
                            logger.info(f"📊 Создано товаров: {created_count}")
                    
                    # Коммитим каждые 500 записей
                    if processed_count % 500 == 0:
                        await self.db.commit()
                        logger.info(f"💾 Промежуточный коммит: {processed_count} товаров обработано")
                
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки товара {product_data.get('name', 'Unknown')}: {e}")
                    error_count += 1
                    continue
            
            # Финальный коммит
            await self.db.commit()
            
            # Обновляем лог синхронизации
            await self.update_sync_log(
                sync_log,
                "success",
                processed_count,
                created_count,
                updated_count,
                error_count
            )
            
            logger.info(f"✅ Синхронизация товаров завершена:")
            logger.info(f"   📊 Обработано: {processed_count}")
            logger.info(f"   ✨ Создано: {created_count}")
            logger.info(f"   🔄 Обновлено: {updated_count}")
            logger.info(f"   ❌ Ошибок: {error_count}")
            
            return {
                "status": "success",
                "records_processed": processed_count,
                "records_created": created_count,
                "records_updated": updated_count,
                "records_errors": error_count
            }
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка синхронизации товаров: {e}")
            await self.update_sync_log(sync_log, "failed", error_details=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0,
                "records_errors": 0
            }
    
    async def sync_customers(self, force: bool = False) -> Dict[str, Any]:
        """Синхронизация контрагентов"""
        if not self.connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("customers", "customer")
        
        try:
            logger.info("🔄 Начинаем синхронизацию контрагентов...")
            
            # Получаем всех контрагентов из МойСклад
            moysklad_customers = await self.connector.get_all_customers()
            
            if not moysklad_customers:
                logger.warning("⚠️ Не получено контрагентов из МойСклад")
                await self.update_sync_log(sync_log, "completed", 0, 0, 0, 0)
                return {
                    "status": "completed", 
                    "message": "No customers found in MoySklad",
                    "records_processed": 0,
                    "records_created": 0,
                    "records_updated": 0,
                    "records_errors": 0
                }
            
            created_count = 0
            updated_count = 0
            error_count = 0
            processed_count = 0
            
            for customer_data in moysklad_customers:
                try:
                    processed_count += 1
                    customer_id = customer_data.get('id')
                    
                    if not customer_id:
                        logger.warning(f"⚠️ Контрагент без ID пропущен: {customer_data.get('name', 'Unknown')}")
                        error_count += 1
                        continue
                    
                    # Проверяем, существует ли контрагент
                    query = select(Customer).where(Customer.moysklad_id == customer_id)
                    result = await self.db.execute(query)
                    existing_customer = result.scalar_one_or_none()
                    
                    # Подготавливаем данные контрагента
                    customer_dict = {
                        'moysklad_id': customer_id,
                        'name': customer_data.get('name', ''),
                        'code': customer_data.get('code', ''),
                        'legal_title': customer_data.get('legalTitle', ''),
                        'email': customer_data.get('email', ''),
                        'phone': customer_data.get('phone', ''),
                        'inn': customer_data.get('inn', ''),
                        'kpp': customer_data.get('kpp', ''),
                        'archived': customer_data.get('archived', False),
                        
                        # Адреса
                        'legal_address': self._safe_get_value(customer_data, 'legalAddress', ''),
                        'actual_address': self._safe_get_value(customer_data, 'actualAddress', ''),
                        
                        # Связанные данные
                        'group_name': self._safe_get_value(customer_data, 'group.name', ''),
                        'discount_percentage': customer_data.get('discountPercentage', 0.0),
                        
                        # Метаданные
                        'updated_at': self._parse_datetime(
                            customer_data.get('updated', '')
                        ) or datetime.now(timezone.utc),
                        'synced_at': datetime.now(timezone.utc)
                    }
                    
                    if existing_customer:
                        # Обновляем существующего контрагента
                        for key, value in customer_dict.items():
                            if hasattr(existing_customer, key):
                                setattr(existing_customer, key, value)
                        
                        updated_count += 1
                        if updated_count % 100 == 0:
                            logger.info(f"📊 Обновлено контрагентов: {updated_count}")
                    else:
                        # Создаем нового контрагента
                        new_customer = Customer(**customer_dict)
                        self.db.add(new_customer)
                        created_count += 1
                        
                        if created_count % 100 == 0:
                            logger.info(f"📊 Создано контрагентов: {created_count}")
                    
                    # Коммитим каждые 500 записей
                    if processed_count % 500 == 0:
                        await self.db.commit()
                        logger.info(f"💾 Промежуточный коммит: {processed_count} контрагентов обработано")
                
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки контрагента {customer_data.get('name', 'Unknown')}: {e}")
                    error_count += 1
                    continue
            
            # Финальный коммит
            await self.db.commit()
            
            # Обновляем лог синхронизации
            await self.update_sync_log(
                sync_log,
                "success", 
                processed_count,
                created_count,
                updated_count,
                error_count
            )
            
            logger.info(f"✅ Синхронизация контрагентов завершена:")
            logger.info(f"   📊 Обработано: {processed_count}")
            logger.info(f"   ✨ Создано: {created_count}")
            logger.info(f"   🔄 Обновлено: {updated_count}")
            logger.info(f"   ❌ Ошибок: {error_count}")
            
            return {
                "status": "success",
                "records_processed": processed_count,
                "records_created": created_count,
                "records_updated": updated_count,
                "records_errors": error_count
            }
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка синхронизации контрагентов: {e}")
            await self.update_sync_log(sync_log, "failed", error_details=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "records_processed": 0,
                "records_created": 0,
                "records_updated": 0,
                "records_errors": 0
            }
    
    async def sync_stores(self) -> Dict[str, Any]:
        """Синхронизация складов"""
        if not self.connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("stores", "store")
        
        try:
            logger.info("🔄 Начинаем синхронизацию складов...")
            
            moysklad_stores = await self.connector.get_all_stores()
            
            created_count = 0
            updated_count = 0
            error_count = 0
            processed_count = 0
            
            for store_data in moysklad_stores:
                try:
                    processed_count += 1
                    store_id = store_data.get('id')
                    
                    if not store_id:
                        error_count += 1
                        continue
                    
                    # Проверяем существование склада
                    query = select(Store).where(Store.moysklad_id == store_id)
                    result = await self.db.execute(query)
                    existing_store = result.scalar_one_or_none()
                    
                    store_dict = {
                        'moysklad_id': store_id,
                        'name': store_data.get('name', ''),
                        'code': store_data.get('code', ''),
                        'address': store_data.get('address', ''),
                        'archived': store_data.get('archived', False),
                        'synced_at': datetime.now(timezone.utc)
                    }
                    
                    if existing_store:
                        for key, value in store_dict.items():
                            if hasattr(existing_store, key):
                                setattr(existing_store, key, value)
                        updated_count += 1
                    else:
                        new_store = Store(**store_dict)
                        self.db.add(new_store)
                        created_count += 1
                
                except Exception as e:
                    logger.error(f"❌ Ошибка обработки склада: {e}")
                    error_count += 1
                    continue
            
            await self.db.commit()
            
            await self.update_sync_log(
                sync_log,
                "success",
                processed_count,
                created_count, 
                updated_count,
                error_count
            )
            
            logger.info(f"✅ Синхронизация складов завершена: создано {created_count}, обновлено {updated_count}")
            
            return {
                "status": "success",
                "records_processed": processed_count,
                "records_created": created_count,
                "records_updated": updated_count,
                "records_errors": error_count
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации складов: {e}")
            await self.update_sync_log(sync_log, "failed", error_details=str(e))
            return {"status": "failed", "error": str(e)}
    
    async def full_sync(self, force: bool = False) -> Dict[str, Any]:
        """Полная синхронизация всех данных"""
        logger.info("🚀 Начинаем полную синхронизацию...")
        
        results = {}
        
        # Синхронизируем склады
        results["stores"] = await self.sync_stores()
        
        # Синхронизируем товары
        results["products"] = await self.sync_products(force)
        
        # Синхронизируем контрагентов
        results["customers"] = await self.sync_customers(force)
        
        # Подсчитываем общую статистику
        total_processed = sum(r.get("records_processed", 0) for r in results.values() if isinstance(r, dict))
        total_created = sum(r.get("records_created", 0) for r in results.values() if isinstance(r, dict))
        total_updated = sum(r.get("records_updated", 0) for r in results.values() if isinstance(r, dict))
        total_errors = sum(r.get("records_errors", 0) for r in results.values() if isinstance(r, dict))
        
        logger.info("🎉 Полная синхронизация завершена:")
        logger.info(f"   📊 Всего обработано: {total_processed}")
        logger.info(f"   ✨ Всего создано: {total_created}")
        logger.info(f"   🔄 Всего обновлено: {total_updated}")
        logger.info(f"   ❌ Всего ошибок: {total_errors}")
        
        return {
            "status": "success",
            "total_processed": total_processed,
            "total_created": total_created,
            "total_updated": total_updated,
            "total_errors": total_errors,
            "details": results
        }