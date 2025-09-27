"""
Улучшенный сервис синхронизации с полным извлечением данных из МойСклад
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.sync_log import SyncLog
from app.models.product import Product
from app.models import StockReport as ProductStock
from app.models.customer import Customer
from app.models.document import Document

logger = logging.getLogger(__name__)

# Create synchronous engine
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
    echo=settings.DEBUG,
    future=True,
)

# Create synchronous session factory
SyncSessionLocal = sessionmaker(bind=sync_engine)


class RateLimiter:
    """Rate limiter для соблюдения лимитов API МойСклад"""
    
    def __init__(self, max_requests=100, time_window=5):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        
    def wait_if_needed(self):
        now = time.time()
        # Удаляем старые запросы
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # Ждем если достигли лимита
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.requests.clear()
        
        self.requests.append(now)


class EnhancedSyncService:
    """Улучшенный сервис синхронизации с полным извлечением данных"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = settings.MOYSKLAD_BASE_URL
        self.token = settings.MOYSKLAD_TOKEN
        self.rate_limiter = RateLimiter()
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }
    
    def create_sync_log(self, sync_type: str, entity_type: str) -> SyncLog:
        """Создание лога синхронизации"""
        sync_log = SyncLog(
            sync_type=sync_type,
            entity_type=entity_type,
            status="in_progress",
            started_at=datetime.utcnow()
        )
        self.db.add(sync_log)
        self.db.commit()
        self.db.refresh(sync_log)
        return sync_log
    
    def update_sync_log(
        self, 
        sync_log: SyncLog, 
        status: str, 
        records_processed: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        records_errors: int = 0,
        error_message: Optional[str] = None
    ):
        """Обновление лога синхронизации"""
        sync_log.status = status
        sync_log.records_processed = records_processed
        sync_log.records_created = records_created
        sync_log.records_updated = records_updated
        sync_log.records_errors = records_errors
        sync_log.error_message = error_message
        sync_log.completed_at = datetime.utcnow()
        self.db.commit()
    
    def make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Выполнение HTTP запроса с rate limiting"""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=self.headers, params=params or {})
                
                # Обработка rate limiting (429)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                    logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                    time.sleep(retry_after / 1000)
                    return self.make_request(endpoint, params)
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error making request to {endpoint}: {e}")
            raise
    
    def get_all_entities(self, endpoint: str, expand: str = None, limit: int = 1000, additional_params: Dict = None) -> List[Dict[str, Any]]:
        """Получение всех сущностей с пагинацией"""
        all_entities = []
        offset = 0
        
        while True:
            params = {"limit": limit, "offset": offset}
            if expand:
                params["expand"] = expand
            if additional_params:
                params.update(additional_params)
            
            try:
                data = self.make_request(endpoint, params)
                rows = data.get("rows", [])
                
                if not rows:
                    break
                
                all_entities.extend(rows)
                offset += len(rows)
                
                # Проверяем есть ли еще данные
                meta = data.get("meta", {})
                if offset >= meta.get("size", 0):
                    break
                    
                # Небольшая задержка между запросами
                time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error fetching entities from {endpoint}: {e}")
                break
        
        return all_entities
    
    def sync_products_enhanced(self, force: bool = False) -> Dict[str, Any]:
        """Улучшенная синхронизация товаров с максимальным извлечением данных"""
        sync_log = self.create_sync_log("products_enhanced", "product")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Получаем товары с максимальным expand
            logger.info("Получаем товары с расширенными данными...")
            products_data = self.get_all_entities(
                "entity/product",
                expand="owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images,attributes,productFolder,country",
                limit=100
            )
            
            logger.info(f"Получено {len(products_data)} товаров")
            
            for product_data in products_data:
                try:
                    records_processed += 1
                    
                    # Извлекаем расширенные данные
                    product_dict = self._extract_enhanced_product_data(product_data)
                    
                    # Проверяем существование товара
                    existing_product = self.db.execute(
                        select(Product).where(Product.external_id == product_data["id"])
                    ).scalar_one_or_none()
                    
                    if existing_product:
                        # Обновляем существующий товар
                        for key, value in product_dict.items():
                            if hasattr(existing_product, key):
                                setattr(existing_product, key, value)
                        existing_product.updated_at = datetime.utcnow()
                        records_updated += 1
                    else:
                        # Создаем новый товар
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        records_created += 1
                    
                    if records_processed % 10 == 0:
                        self.db.commit()
                        logger.info(f"Обработано товаров: {records_processed}")
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing product {product_data.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            logger.info(f"Синхронизация товаров завершена: обработано {records_processed}, создано {records_created}, обновлено {records_updated}, ошибок {records_errors}")
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in enhanced products sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def _extract_enhanced_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Извлечение расширенных данных товара"""
        
        # Базовые поля
        product_dict = {
            "external_id": product_data["id"],
            "name": product_data.get("name", ""),
            "code": product_data.get("code", ""),
            "article": product_data.get("article", ""),
            "description": product_data.get("description", ""),
            "archived": product_data.get("archived", False),
            "external_raw": json.dumps(product_data, ensure_ascii=False)
        }
        
        # Цены
        buy_price_data = product_data.get("buyPrice", {})
        if buy_price_data:
            product_dict["buy_price"] = buy_price_data.get("value", 0)
            currency = buy_price_data.get("currency", {})
            if currency:
                currency_name = currency.get("name", "")
                product_dict["currency"] = currency_name[:3].upper() if currency_name else "RUB"
        
        # Цены продажи (берем первую цену)
        sale_prices = product_data.get("salePrices", [])
        if sale_prices and len(sale_prices) > 0:
            product_dict["sale_price"] = sale_prices[0].get("value", 0)
        
        # Единица измерения
        uom = product_data.get("uom", {})
        if uom:
            uom_name = uom.get("name", "")
            product_dict["uom"] = uom_name[:10] if uom_name else None
        
        # Группа товаров
        group = product_data.get("group", {})
        if group:
            product_dict["group_name"] = group.get("name", "")
        
        # Поставщик
        supplier = product_data.get("supplier", {})
        if supplier:
            product_dict["supplier_name"] = supplier.get("name", "")
        
        # Папка товара
        product_folder = product_data.get("productFolder", {})
        if product_folder:
            product_dict["group_name"] = product_folder.get("name", "")
        
        # Страна
        country = product_data.get("country", {})
        if country:
            product_dict["country"] = country.get("name", "")
        
        # Дополнительные поля
        product_dict["weight"] = product_data.get("weight", 0)
        product_dict["volume"] = product_data.get("volume", 0)
        product_dict["tracking_type"] = product_data.get("trackingType", "")
        product_dict["is_serial_trackable"] = product_data.get("isSerialTrackable", False)
        
        return product_dict
    
    def sync_services(self) -> Dict[str, Any]:
        """Синхронизация услуг"""
        sync_log = self.create_sync_log("services", "service")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем услуги...")
            services_data = self.get_all_entities("entity/service")
            
            logger.info(f"Получено {len(services_data)} услуг")
            
            for service_data in services_data:
                try:
                    records_processed += 1
                    
                    # Создаем товар из услуги (услуги тоже товары в нашей модели)
                    product_dict = {
                        "external_id": service_data["id"],
                        "name": service_data.get("name", ""),
                        "code": service_data.get("code", ""),
                        "article": service_data.get("article", ""),
                        "description": service_data.get("description", ""),
                        "archived": service_data.get("archived", False),
                        "external_raw": json.dumps(service_data, ensure_ascii=False),
                        "is_service": True  # Помечаем как услугу
                    }
                    
                    # Цены продажи
                    sale_prices = service_data.get("salePrices", [])
                    if sale_prices and len(sale_prices) > 0:
                        product_dict["sale_price"] = sale_prices[0].get("value", 0)
                    
                    # Проверяем существование
                    existing_product = self.db.execute(
                        select(Product).where(Product.external_id == service_data["id"])
                    ).scalar_one_or_none()
                    
                    if existing_product:
                        for key, value in product_dict.items():
                            if hasattr(existing_product, key):
                                setattr(existing_product, key, value)
                        records_updated += 1
                    else:
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        records_created += 1
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing service {service_data.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in services sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_bundles(self) -> Dict[str, Any]:
        """Синхронизация комплектов"""
        sync_log = self.create_sync_log("bundles", "bundle")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем комплекты...")
            bundles_data = self.get_all_entities("entity/bundle")
            
            logger.info(f"Получено {len(bundles_data)} комплектов")
            
            for bundle_data in bundles_data:
                try:
                    records_processed += 1
                    
                    # Создаем товар из комплекта
                    product_dict = {
                        "external_id": bundle_data["id"],
                        "name": bundle_data.get("name", ""),
                        "code": bundle_data.get("code", ""),
                        "article": bundle_data.get("article", ""),
                        "description": bundle_data.get("description", ""),
                        "archived": bundle_data.get("archived", False),
                        "external_raw": json.dumps(bundle_data, ensure_ascii=False),
                        "is_bundle": True  # Помечаем как комплект
                    }
                    
                    # Цены продажи
                    sale_prices = bundle_data.get("salePrices", [])
                    if sale_prices and len(sale_prices) > 0:
                        product_dict["sale_price"] = sale_prices[0].get("value", 0)
                    
                    # Проверяем существование
                    existing_product = self.db.execute(
                        select(Product).where(Product.external_id == bundle_data["id"])
                    ).scalar_one_or_none()
                    
                    if existing_product:
                        for key, value in product_dict.items():
                            if hasattr(existing_product, key):
                                setattr(existing_product, key, value)
                        records_updated += 1
                    else:
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        records_created += 1
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing bundle {bundle_data.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in bundles sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_stores(self) -> Dict[str, Any]:
        """Синхронизация складов"""
        sync_log = self.create_sync_log("stores", "store")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем склады...")
            stores_data = self.get_all_entities("entity/store")
            
            logger.info(f"Получено {len(stores_data)} складов")
            
            # Создаем таблицу складов если не существует
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS stores (
                    id SERIAL PRIMARY KEY,
                    external_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    code VARCHAR(255),
                    address TEXT,
                    archived BOOLEAN DEFAULT FALSE,
                    external_raw JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            for store_data in stores_data:
                try:
                    records_processed += 1
                    
                    store_dict = {
                        "external_id": store_data["id"],
                        "name": store_data.get("name", ""),
                        "code": store_data.get("externalCode", ""),
                        "address": store_data.get("address", ""),
                        "archived": store_data.get("archived", False),
                        "external_raw": json.dumps(store_data, ensure_ascii=False)
                    }
                    
                    # Проверяем существование
                    existing_store = self.db.execute(
                        text("SELECT id FROM stores WHERE external_id = :external_id"),
                        {"external_id": store_data["id"]}
                    ).fetchone()
                    
                    if existing_store:
                        # Обновляем
                        self.db.execute(text("""
                            UPDATE stores SET 
                                name = :name, code = :code, address = :address, 
                                archived = :archived, external_raw = :external_raw,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE external_id = :external_id
                        """), {**store_dict, "external_id": store_data["id"]})
                        records_updated += 1
                    else:
                        # Создаем
                        self.db.execute(text("""
                            INSERT INTO stores (external_id, name, code, address, archived, external_raw)
                            VALUES (:external_id, :name, :code, :address, :archived, :external_raw)
                        """), store_dict)
                        records_created += 1
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing store {store_data.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in stores sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_currencies(self) -> Dict[str, Any]:
        """Синхронизация валют"""
        sync_log = self.create_sync_log("currencies", "currency")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем валюты...")
            currencies_data = self.get_all_entities("entity/currency")
            
            logger.info(f"Получено {len(currencies_data)} валют")
            
            # Создаем таблицу валют если не существует
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS currencies (
                    id SERIAL PRIMARY KEY,
                    external_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255),
                    code VARCHAR(10),
                    iso_code VARCHAR(10),
                    rate DECIMAL(15,4),
                    is_default BOOLEAN DEFAULT FALSE,
                    external_raw JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            for currency_data in currencies_data:
                try:
                    records_processed += 1
                    
                    currency_dict = {
                        "external_id": currency_data["id"],
                        "name": currency_data.get("name", ""),
                        "full_name": currency_data.get("fullName", ""),
                        "code": currency_data.get("code", ""),
                        "iso_code": currency_data.get("isoCode", ""),
                        "rate": currency_data.get("rate", 0),
                        "is_default": currency_data.get("default", False),
                        "external_raw": json.dumps(currency_data, ensure_ascii=False)
                    }
                    
                    # Проверяем существование
                    existing_currency = self.db.execute(
                        text("SELECT id FROM currencies WHERE external_id = :external_id"),
                        {"external_id": currency_data["id"]}
                    ).fetchone()
                    
                    if existing_currency:
                        # Обновляем
                        self.db.execute(text("""
                            UPDATE currencies SET 
                                name = :name, full_name = :full_name, code = :code, 
                                iso_code = :iso_code, rate = :rate, is_default = :is_default,
                                external_raw = :external_raw, updated_at = CURRENT_TIMESTAMP
                            WHERE external_id = :external_id
                        """), {**currency_dict, "external_id": currency_data["id"]})
                        records_updated += 1
                    else:
                        # Создаем
                        self.db.execute(text("""
                            INSERT INTO currencies (external_id, name, full_name, code, iso_code, rate, is_default, external_raw)
                            VALUES (:external_id, :name, :full_name, :code, :iso_code, :rate, :is_default, :external_raw)
                        """), currency_dict)
                        records_created += 1
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing currency {currency_data.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in currencies sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_turnover_reports(self) -> Dict[str, Any]:
        """Синхронизация отчетов по оборотам товаров"""
        sync_log = self.create_sync_log("turnover", "report")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем отчеты по оборотам...")
            turnover_data = self.get_all_entities("report/turnover/all")
            
            logger.info(f"Получено {len(turnover_data)} записей оборотов")
            
            # Создаем таблицу оборотов если не существует
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS product_turnover (
                    id SERIAL PRIMARY KEY,
                    product_external_id VARCHAR(255) NOT NULL,
                    product_name VARCHAR(500),
                    product_code VARCHAR(100),
                    stock_at_period_start DECIMAL(10,3),
                    income DECIMAL(10,3),
                    outcome DECIMAL(10,3),
                    stock_at_period_end DECIMAL(10,3),
                    external_raw JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            for turnover_item in turnover_data:
                try:
                    records_processed += 1
                    
                    # Извлекаем ID товара из meta.href
                    meta_href = turnover_item.get("meta", {}).get("href", "")
                    product_external_id = meta_href.split("/")[-1] if meta_href else ""
                    
                    turnover_dict = {
                        "product_external_id": product_external_id,
                        "product_name": turnover_item.get("name", ""),
                        "product_code": turnover_item.get("code", ""),
                        "stock_at_period_start": turnover_item.get("stockAtPeriodStart", 0),
                        "income": turnover_item.get("income", 0),
                        "outcome": turnover_item.get("outcome", 0),
                        "stock_at_period_end": turnover_item.get("stockAtPeriodEnd", 0),
                        "external_raw": json.dumps(turnover_item, ensure_ascii=False)
                    }
                    
                    # Проверяем существование
                    existing_turnover = self.db.execute(
                        text("SELECT id FROM product_turnover WHERE product_external_id = :product_external_id"),
                        {"product_external_id": product_external_id}
                    ).fetchone()
                    
                    if existing_turnover:
                        # Обновляем
                        self.db.execute(text("""
                            UPDATE product_turnover SET 
                                product_name = :product_name, product_code = :product_code,
                                stock_at_period_start = :stock_at_period_start, income = :income,
                                outcome = :outcome, stock_at_period_end = :stock_at_period_end,
                                external_raw = :external_raw, updated_at = CURRENT_TIMESTAMP
                            WHERE product_external_id = :product_external_id
                        """), {**turnover_dict, "product_external_id": product_external_id})
                        records_updated += 1
                    else:
                        # Создаем
                        self.db.execute(text("""
                            INSERT INTO product_turnover (product_external_id, product_name, product_code,
                                stock_at_period_start, income, outcome, stock_at_period_end, external_raw)
                            VALUES (:product_external_id, :product_name, :product_code,
                                :stock_at_period_start, :income, :outcome, :stock_at_period_end, :external_raw)
                        """), turnover_dict)
                        records_created += 1
                        
                except Exception as e:
                    records_errors += 1
                    logger.error(f"Error processing turnover item {turnover_item.get('name', 'Unknown')}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in turnover reports sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_retail_documents(self) -> Dict[str, Any]:
        """Синхронизация розничных документов"""
        sync_log = self.create_sync_log("retail_documents", "document")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Розничные документы
            retail_doc_types = [
                ("retaildemand", "Розничные продажи"),
                ("retailsalesreturn", "Возвраты розничных продаж")
            ]
            
            for doc_type, doc_description in retail_doc_types:
                logger.info(f"Получаем {doc_description}...")
                try:
                    documents = self.get_all_entities(f"entity/{doc_type}")
                    logger.info(f"Получено {len(documents)} документов типа {doc_type}")
                    
                    for doc_data in documents:
                        try:
                            records_processed += 1
                            
                            doc_dict = {
                                "external_id": doc_data["id"],
                                "name": doc_data.get("name", ""),
                                "moment": self._parse_datetime(doc_data.get("moment")),
                                "sum": doc_data.get("sum", 0),
                                "applicable": doc_data.get("applicable", False),
                                "document_type": doc_type,
                                "external_raw": json.dumps(doc_data, ensure_ascii=False)
                            }
                            
                            # Проверяем существование
                            existing_doc = self.db.execute(
                                text("SELECT id FROM documents WHERE external_id = :external_id"),
                                {"external_id": doc_data["id"]}
                            ).fetchone()
                            
                            if existing_doc:
                                # Обновляем
                                self.db.execute(text("""
                                    UPDATE documents SET 
                                        name = :name, moment = :moment, sum = :sum,
                                        applicable = :applicable, document_type = :document_type,
                                        external_raw = :external_raw, updated_at = CURRENT_TIMESTAMP
                                    WHERE external_id = :external_id
                                """), {**doc_dict, "external_id": doc_data["id"]})
                                records_updated += 1
                            else:
                                # Создаем
                                self.db.execute(text("""
                                    INSERT INTO documents (external_id, name, moment, sum, applicable, document_type, external_raw)
                                    VALUES (:external_id, :name, :moment, :sum, :applicable, :document_type, :external_raw)
                                """), {**doc_dict, "external_id": doc_data["id"]})
                                records_created += 1
                                
                        except Exception as e:
                            records_errors += 1
                            logger.error(f"Error processing {doc_type} document {doc_data.get('name', 'Unknown')}: {e}")
                            
                except Exception as e:
                    logger.error(f"Error fetching {doc_type}: {e}")
            
            self.db.commit()
            
            self.update_sync_log(
                sync_log, "success", records_processed, records_created, records_updated, records_errors
            )
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in retail documents sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def sync_employee_context(self) -> Dict[str, Any]:
        """Синхронизация контекста сотрудника"""
        sync_log = self.create_sync_log("employee_context", "context")
        
        try:
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            logger.info("Получаем информацию о сотруднике...")
            
            # Получаем информацию о текущем сотруднике
            employee_data = self.make_request("context/employee")
            
            # Создаем таблицу сотрудников если не существует
            self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    external_id VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    position VARCHAR(255),
                    external_raw JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            employee_dict = {
                "external_id": employee_data.get("id", ""),
                "name": employee_data.get("name", ""),
                "email": employee_data.get("email", ""),
                "position": employee_data.get("position", ""),
                "external_raw": json.dumps(employee_data, ensure_ascii=False)
            }
            
            records_processed = 1
            
            # Проверяем существование
            existing_employee = self.db.execute(
                text("SELECT id FROM employees WHERE external_id = :external_id"),
                {"external_id": employee_data.get("id", "")}
            ).fetchone()
            
            if existing_employee:
                # Обновляем
                self.db.execute(text("""
                    UPDATE employees SET 
                        name = :name, email = :email, position = :position,
                        external_raw = :external_raw, updated_at = CURRENT_TIMESTAMP
                    WHERE external_id = :external_id
                """), {**employee_dict, "external_id": employee_data.get("id", "")})
                records_updated = 1
            else:
                # Создаем
                self.db.execute(text("""
                    INSERT INTO employees (external_id, name, email, position, external_raw)
                    VALUES (:external_id, :name, :email, :position, :external_raw)
                """), employee_dict)
                records_created = 1
            
            self.db.commit()
            
            self.update_sync_log(sync_log, "success", records_processed, records_created, records_updated, records_errors)
            
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors
            }
            
        except Exception as e:
            logger.error(f"Error in employee context sync: {e}")
            self.update_sync_log(sync_log, "error", records_processed, records_created, records_updated, records_errors, str(e))
            return {"error": str(e), "sync_id": sync_log.id}
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """Парсинг даты и времени"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except:
            return None
    
    def full_enhanced_sync(self, force: bool = False) -> Dict[str, Any]:
        """Полная улучшенная синхронизация всех доступных данных"""
        logger.info("Начинаем полную улучшенную синхронизацию...")
        
        results = {}
        
        try:
            # 1. Синхронизация контекста
            logger.info("1. Синхронизация контекста...")
            results["employee_context"] = self.sync_employee_context()
            
            # 2. Синхронизация справочников
            logger.info("2. Синхронизация справочников...")
            results["stores"] = self.sync_stores()
            results["currencies"] = self.sync_currencies()
            
            # 3. Синхронизация товаров, услуг и комплектов
            logger.info("3. Синхронизация товаров, услуг и комплектов...")
            results["products_enhanced"] = self.sync_products_enhanced(force)
            results["services"] = self.sync_services()
            results["bundles"] = self.sync_bundles()
            
            # 4. Синхронизация остатков (используем существующий метод)
            logger.info("4. Синхронизация остатков...")
            from app.services.sync_sync import SyncSyncService
            sync_service = SyncSyncService(self.db)
            results["stock"] = sync_service.sync_stock(force)
            
            # 5. Синхронизация клиентов (используем существующий метод)
            logger.info("5. Синхронизация клиентов...")
            results["customers"] = sync_service.sync_customers(force)
            
            # 6. Синхронизация документов (используем существующий метод)
            logger.info("6. Синхронизация документов...")
            results["documents"] = sync_service.sync_documents(force)
            
            # 7. Синхронизация розничных документов
            logger.info("7. Синхронизация розничных документов...")
            results["retail_documents"] = self.sync_retail_documents()
            
            # 8. Синхронизация отчетов по оборотам
            logger.info("8. Синхронизация отчетов по оборотам...")
            results["turnover_reports"] = self.sync_turnover_reports()
            
            logger.info("Полная улучшенная синхронизация завершена!")
            
            return {
                "status": "success",
                "message": "Full enhanced sync completed with additional endpoints",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in full enhanced sync: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": results
            }
