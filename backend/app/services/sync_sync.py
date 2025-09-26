"""
Synchronous version of sync service for Celery tasks
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.sync_log import SyncLog
from app.models.product import Product
from app.models.customer import Customer
from app.models.document import Document
from app.models.document import Document
from app.connectors.moysklad import MoySkladConnector

logger = logging.getLogger(__name__)

# Create synchronous engine
sync_engine = create_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"),
    echo=settings.DEBUG,
    future=True,
)

# Create synchronous session factory
SyncSessionLocal = sessionmaker(bind=sync_engine)


class SyncSyncService:
    """Synchronous version of sync service for Celery tasks"""
    
    def __init__(self, db: Session):
        self.db = db
        self.moysklad_connector = MoySkladConnector()
    
    def create_sync_log(self, sync_type: str, entity_type: str) -> SyncLog:
        """Create sync log entry"""
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
        """Update sync log entry"""
        sync_log.status = status
        sync_log.records_processed = records_processed
        sync_log.records_created = records_created
        sync_log.records_updated = records_updated
        sync_log.records_errors = records_errors
        sync_log.error_message = error_message
        sync_log.completed_at = datetime.utcnow()
        self.db.commit()
    
    def sync_products(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize products from MoySklad"""
        if not self.moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = self.create_sync_log("products", "product")
        
        try:
            # Initialize counters
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Get last sync time for incremental sync
            last_sync = None
            if not force:
                last_sync_log = self.db.execute(
                    select(SyncLog)
                    .where(SyncLog.sync_type == "products")
                    .where(SyncLog.status == "success")
                    .order_by(SyncLog.completed_at.desc())
                    .limit(1)  # Only get the most recent one
                )
                last_sync_result = last_sync_log.scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at
            
            # Fetch products from MoySklad (sync version)
            products_data = self._get_products_sync(updated_since=last_sync)
            
            for product_data in products_data:
                try:
                    records_processed += 1
                    
                    # Check if product exists
                    existing_product = self.db.execute(
                        select(Product).where(Product.external_id == product_data["id"])
                    )
                    existing_product = existing_product.scalar_one_or_none()
                    
                    # Prepare product data
                    product_dict = {
                        "external_id": product_data["id"],
                        "name": product_data.get("name", ""),
                        "code": product_data.get("code", ""),
                        "article": product_data.get("article", ""),
                        "description": product_data.get("description", ""),
                        "archived": product_data.get("archived", False),
                        "buy_price": None,
                        "sale_price": None,
                        "currency": None,
                        "uom": None,
                        "group_name": None,
                        "supplier_name": None,
                        "external_raw": json.dumps(product_data, ensure_ascii=False),
                        "external_updated": product_data.get("updated")
                    }
                    
                    # Extract buy price
                    if "buyPrice" in product_data:
                        buy_price = product_data["buyPrice"]
                        if buy_price and "value" in buy_price:
                            product_dict["buy_price"] = float(buy_price["value"]) / 100
                    
                    # Extract sale price (first one)
                    if "salePrices" in product_data and product_data["salePrices"]:
                        sale_price = product_data["salePrices"][0]
                        if "value" in sale_price:
                            product_dict["sale_price"] = float(sale_price["value"]) / 100
                    
                    # Extract currency with length limit
                    if "buyPrice" in product_data and product_data["buyPrice"]:
                        currency = product_data["buyPrice"].get("currency", {})
                        if currency:
                            currency_name = currency.get("name")
                            # Ограничиваем валюту до 3 символов для базы данных
                            product_dict["currency"] = currency_name[:3].upper() if currency_name else "RUB"
                    
                    # Extract UOM with length limit
                    if "uom" in product_data and product_data["uom"]:
                        uom_name = product_data["uom"].get("name")
                        # Ограничиваем UOM до 10 символов для базы данных
                        product_dict["uom"] = uom_name[:10] if uom_name else None
                    
                    # Extract group
                    if "productFolder" in product_data and product_data["productFolder"]:
                        product_dict["group_name"] = product_data["productFolder"].get("name")
                    
                    # Extract supplier
                    if "supplier" in product_data and product_data["supplier"]:
                        product_dict["supplier_name"] = product_data["supplier"].get("name")
                    
                    if existing_product:
                        # Update existing product
                        for key, value in product_dict.items():
                            if hasattr(existing_product, key):
                                setattr(existing_product, key, value)
                        records_updated += 1
                    else:
                        # Create new product
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        records_created += 1
                    
                    # Commit every 100 records
                    if records_processed % 100 == 0:
                        self.db.commit()
                        logger.info(f"Processed {records_processed} products...")
                        
                except Exception as e:
                    logger.error(f"Error processing product {product_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            self.update_sync_log(
                sync_log, 
                "success", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors
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
            logger.error(f"Error syncing products: {e}")
            self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    def _get_products_sync(self, updated_since: Optional[datetime] = None) -> list:
        """Get products from MoySklad synchronously with expanded data"""
        import httpx
        import time
        
        all_products = []
        offset = 0
        limit = 100  # Уменьшаем лимит при использовании expand
        
        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }
        
        while True:
            params = {
                "limit": limit,
                "offset": offset,
                # Расширяем данные для получения связанной информации
                "expand": "owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images,attributes"
            }
            
            if updated_since:
                # Format date for MoySklad API (YYYY-MM-DD HH:MM:SS)
                formatted_date = updated_since.strftime("%Y-%m-%d %H:%M:%S")
                params["filter"] = f"updated>={formatted_date}"
            
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/product",
                        headers=headers,
                        params=params
                    )
                    
                    # Обработка rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                        logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                        time.sleep(retry_after / 1000)
                        continue
                    
                    logger.info(f"API Response Status: {response.status_code}")
                    
                    response.raise_for_status()
                    
                    data = response.json()
                rows = data.get("rows", [])
                
                if not rows:
                    break
                
                all_products.extend(rows)
                offset += limit
                
                # Улучшенный rate limiting
                time.sleep(0.02)  # Более частые запросы как в рабочем скрипте
                
                # Check if we have more data
                meta = data.get("meta", {})
                if offset >= meta.get("size", 0):
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching products at offset {offset}: {e}")
                break
        
        return all_products
    
    def sync_customers(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize customers from MoySklad"""
        if not self.moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = self.create_sync_log("customers", "counterparty")
        
        try:
            # Initialize counters
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Get last sync time for incremental sync
            last_sync = None
            if not force:
                last_sync_log = self.db.execute(
                    select(SyncLog)
                    .where(SyncLog.sync_type == "customers")
                    .where(SyncLog.status == "success")
                    .order_by(SyncLog.completed_at.desc())
                    .limit(1)  # Only get the most recent one
                )
                last_sync_result = last_sync_log.scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at
            
            # Fetch customers from MoySklad (sync version)
            customers_data = self._get_customers_sync(updated_since=last_sync)
            
            for customer_data in customers_data:
                try:
                    records_processed += 1
                    
                    # Check if customer exists
                    existing_customer = self.db.execute(
                        select(Customer).where(Customer.external_id == customer_data["id"])
                    )
                    existing_customer = existing_customer.scalar_one_or_none()
                    
                    # Prepare customer data
                    email = customer_data.get("email", "")
                    if not email or email.strip() == "":
                        email = None
                        
                    customer_dict = {
                        "external_id": customer_data["id"],
                        "name": customer_data.get("name", ""),
                        "code": customer_data.get("code", ""),
                        "legal_title": customer_data.get("legalTitle", ""),
                        "email": email,
                        "phone": customer_data.get("phone", ""),
                        "inn": customer_data.get("inn", ""),
                        "kpp": customer_data.get("kpp", ""),
                        "address": customer_data.get("legalAddress", ""),
                        "postal_address": customer_data.get("actualAddress", ""),
                        "archived": customer_data.get("archived", False),
                        "external_raw": json.dumps(customer_data, ensure_ascii=False),
                        "external_updated": customer_data.get("updated")
                    }
                    
                    if existing_customer:
                        # Update existing customer
                        for key, value in customer_dict.items():
                            if hasattr(existing_customer, key):
                                setattr(existing_customer, key, value)
                        records_updated += 1
                    else:
                        # Create new customer
                        new_customer = Customer(**customer_dict)
                        self.db.add(new_customer)
                        records_created += 1
                    
                    # Commit every 100 records
                    if records_processed % 100 == 0:
                        self.db.commit()
                        logger.info(f"Processed {records_processed} customers...")
                        
                except Exception as e:
                    logger.error(f"Error processing customer {customer_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            self.update_sync_log(
                sync_log, 
                "success", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors
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
            logger.error(f"Error syncing customers: {e}")
            self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    def _get_customers_sync(self, updated_since: Optional[datetime] = None) -> list:
        """Get customers from MoySklad synchronously"""
        import httpx
        import time
        
        all_customers = []
        offset = 0
        limit = 1000
        
        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }
        
        while True:
            params = {
                "limit": limit,
                "offset": offset
            }
            
            if updated_since:
                # Format date for MoySklad API (YYYY-MM-DD HH:MM:SS)
                formatted_date = updated_since.strftime("%Y-%m-%d %H:%M:%S")
                params["filter"] = f"updated>={formatted_date}"
            
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/counterparty",
                        headers=headers,
                        params=params
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                rows = data.get("rows", [])
                
                if not rows:
                    break
                
                all_customers.extend(rows)
                offset += limit
                
                # Rate limiting
                time.sleep(0.1)
                
                # Check if we have more data
                meta = data.get("meta", {})
                if offset >= meta.get("size", 0):
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching customers at offset {offset}: {e}")
                break
        
        return all_customers
    
    def sync_documents(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize documents from MoySklad synchronously."""
        if not self.moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}

        sync_log = self.create_sync_log("documents", "customerorder")

        records_processed = 0
        records_created = 0
        records_updated = 0
        records_errors = 0

        try:
            last_sync = None
            if not force:
                last_sync_result = self.db.execute(
                    text(
                        "SELECT * FROM sync_logs WHERE sync_type = :sync_type AND status = :status ORDER BY completed_at DESC LIMIT 1"
                    ),
                    {"sync_type": "documents", "status": "success"},
                ).scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at

            # Sync different document types
            document_types = [
                ("customerorder", "Заказ покупателя"),
                ("demand", "Отгрузка"),
                ("salesreturn", "Возврат покупателя"),
                ("purchaseorder", "Заказ поставщику"),
                ("receipt", "Приходная накладная"),
                ("purchasereturn", "Возврат поставщику")
            ]
            
            for doc_type, doc_name in document_types:
                try:
                    documents_data = self._get_documents_sync(doc_type, updated_since=last_sync)
                    
                    for document_data in documents_data:
                        records_processed += 1
                        
                        # Check if document exists
                        existing_document = self.db.execute(
                            text("SELECT * FROM documents WHERE external_id = :external_id"),
                            {"external_id": document_data["id"]},
                        ).scalar_one_or_none()

                        # Prepare document data
                        document_dict = {
                            "external_id": document_data["id"],
                            "name": document_data.get("name", ""),
                            "document_type": doc_name,
                            "moment": self._parse_datetime(document_data.get("moment")),
                            "sum": self._parse_decimal(document_data.get("sum", 0)),
                            "currency": document_data.get("currency", {}).get("name", "RUB"),
                            "applicable": document_data.get("applicable", False),
                            "state_name": document_data.get("state", {}).get("name"),
                            "customer_id": self._get_customer_id_by_external_id(
                                document_data.get("agent", {}).get("id")
                            ),
                            "organization_name": document_data.get("organization", {}).get("name"),
                            "store_name": document_data.get("store", {}).get("name"),
                            "external_raw": json.dumps(document_data, ensure_ascii=False),
                            "external_updated": self._parse_datetime(document_data.get("updated"))
                        }

                        if existing_document:
                            # Update existing document
                            for key, value in document_dict.items():
                                if hasattr(existing_document, key):
                                    setattr(existing_document, key, value)
                            self.db.add(existing_document)
                            records_updated += 1
                        else:
                            # Create new document
                            new_document = Document(**document_dict)
                            self.db.add(new_document)
                            records_created += 1
                        
                        # Commit every 100 records
                        if records_processed % 100 == 0:
                            self.db.commit()
                            logger.info(f"Processed {records_processed} documents...")
                            
                except Exception as e:
                    logger.error(f"Error processing document type {doc_type}: {e}")
                    records_errors += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            self.update_sync_log(
                sync_log,
                "success",
                records_processed,
                records_created,
                records_updated,
                records_errors,
            )
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors,
            }

        except Exception as e:
            logger.error(f"Error syncing documents: {e}")
            self.db.rollback()
            self.update_sync_log(
                sync_log,
                "error",
                records_processed,
                records_created,
                records_updated,
                records_errors,
                str(e),
            )
            return {"error": str(e), "sync_id": sync_log.id}

    def sync_stock(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize stock from MoySklad synchronously."""
        if not self.moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}

        sync_log = self.create_sync_log("stock", "stock")

        records_processed = 0
        records_created = 0
        records_updated = 0
        records_errors = 0

        try:
            # Get stock data from MoySklad
            stock_data = self._get_stock_sync()
            
            for stock_item in stock_data:
                records_processed += 1
                
                try:
                    # Log stock item structure for debugging
                    logger.info(f"Processing stock item: {json.dumps(stock_item, ensure_ascii=False)[:500]}")
                    
                    # Extract product ID from different sources depending on endpoint
                    product_external_id = None
                    
                    # Try meta.href first (for report/stock/all and report/stock/bystore)
                    meta_href = stock_item.get("meta", {}).get("href", "")
                    if meta_href:
                        # Extract UUID from href like: https://api.moysklad.ru/api/remap/1.2/entity/product/7192ee4a-953f-11f0-0a80-0729000b0f7c
                        product_external_id = meta_href.split("/")[-1].split("?")[0]
                    
                    # Try assortmentId (for report/stock/all/current)
                    if not product_external_id and "assortmentId" in stock_item:
                        product_external_id = stock_item["assortmentId"]
                    
                    logger.info(f"Looking for product with external_id: {product_external_id}")
                    
                    if not product_external_id:
                        logger.warning(f"No product ID found in stock item: {stock_item}")
                        continue
                    
                    product = self.db.execute(
                        text("SELECT * FROM products WHERE external_id = :external_id"),
                        {"external_id": product_external_id},
                    ).first()
                    
                    if product:
                        logger.info(f"Found product: {product.name} (ID: {product.id})")
                        # Update or create stock record
                        existing_stock = self.db.execute(
                            text("SELECT * FROM product_stock WHERE product_id = :product_id"),
                            {"product_id": product.id},
                        ).first()
                        
                        # Prepare stock data - handle different endpoints
                        # For report/stock/all and report/stock/all/current, data is directly in the item
                        total_stock = self._parse_decimal(stock_item.get("stock", 0))
                        total_reserve = self._parse_decimal(stock_item.get("reserve", 0))
                        total_in_transit = self._parse_decimal(stock_item.get("inTransit", 0))
                        total_available = self._parse_decimal(stock_item.get("quantity", stock_item.get("available", 0)))
                        
                        store_name = ""
                        store_id = ""
                        
                        # For report/stock/bystore, data comes in stockByStore array
                        stock_by_store = stock_item.get("stockByStore", [])
                        if stock_by_store:
                            # Безопасное суммирование с обработкой None значений
                            def safe_sum(values):
                                return sum(v for v in values if v is not None)
                            
                            total_stock = safe_sum([self._parse_decimal(store.get("stock", 0)) for store in stock_by_store])
                            total_reserve = safe_sum([self._parse_decimal(store.get("reserve", 0)) for store in stock_by_store])
                            total_in_transit = safe_sum([self._parse_decimal(store.get("inTransit", 0)) for store in stock_by_store])
                            total_available = safe_sum([self._parse_decimal(store.get("available", 0)) for store in stock_by_store])
                            
                            # Get store info from first store (or empty if no stores)
                            store_name = stock_by_store[0].get("store", {}).get("name", "") if stock_by_store else ""
                            store_id = stock_by_store[0].get("store", {}).get("id", "") if stock_by_store else ""
                        
                        stock_dict = {
                            "product_id": product.id,
                            "stock": total_stock,
                            "reserve": total_reserve,
                            "in_transit": total_in_transit,
                            "available": total_available,
                            "store_name": store_name,
                            "store_id": store_id
                        }
                        
                        if existing_stock:
                            # Update existing stock using SQL UPDATE
                            update_data = {k: v for k, v in stock_dict.items() if k != 'product_id'}
                            self.db.execute(
                                text("""
                                    UPDATE product_stock 
                                    SET stock=:stock, reserve=:reserve, in_transit=:in_transit, 
                                        available=:available, store_name=:store_name, store_id=:store_id,
                                        updated_at=now()
                                    WHERE product_id=:product_id
                                """),
                                {**update_data, 'product_id': product.id}
                            )
                            records_updated += 1
                        else:
                            # Create new stock record using SQL INSERT
                            self.db.execute(
                                text("""
                                    INSERT INTO product_stock 
                                    (product_id, stock, reserve, in_transit, available, store_name, store_id, created_at, updated_at)
                                    VALUES (:product_id, :stock, :reserve, :in_transit, :available, :store_name, :store_id, now(), now())
                                """),
                                stock_dict
                            )
                            records_created += 1
                    
                    # Commit every 100 records
                    if records_processed % 100 == 0:
                        self.db.commit()
                        logger.info(f"Processed {records_processed} stock records...")
                        
                except Exception as e:
                    logger.error(f"Error processing stock item: {e}")
                    records_errors += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            self.update_sync_log(
                sync_log,
                "success",
                records_processed,
                records_created,
                records_updated,
                records_errors,
            )
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors,
            }

        except Exception as e:
            logger.error(f"Error syncing stock: {e}")
            self.db.rollback()
            self.update_sync_log(
                sync_log,
                "error",
                records_processed,
                records_created,
                records_updated,
                records_errors,
                str(e),
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    def full_sync(self, force: bool = False) -> Dict[str, Any]:
        """Perform full synchronization"""
        results = {}
        
        try:
            # Sync products
            results["products"] = self.sync_products(force)
            
            # Sync customers
            results["customers"] = self.sync_customers(force)
            
            # Sync documents
            results["documents"] = self.sync_documents(force)
            
            # Sync stock
            results["stock"] = self.sync_stock(force)
            
            return {
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in full sync: {e}")
            return {
                "status": "error",
                "error": str(e),
                "results": results
            }
    
    def sync_stores(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize stores from MoySklad synchronously."""
        if not self.moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}

        sync_log = self.create_sync_log("stores", "store")

        records_processed = 0
        records_created = 0
        records_updated = 0
        records_errors = 0

        try:
            stores_data = self._get_stores_sync()
            
            for store_data in stores_data:
                records_processed += 1
                
                try:
                    # Check if store exists
                    existing_store = self.db.execute(
                        text("SELECT * FROM stores WHERE external_id = :external_id"),
                        {"external_id": store_data["id"]},
                    ).scalar_one_or_none()

                    # Prepare store data
                    store_dict = {
                        "external_id": store_data["id"],
                        "name": store_data.get("name", ""),
                        "code": store_data.get("code", ""),
                        "archived": store_data.get("archived", False),
                        "external_raw": json.dumps(store_data, ensure_ascii=False),
                        "external_updated": self._parse_datetime(store_data.get("updated"))
                    }

                    if existing_store:
                        # Update existing store
                        for key, value in store_dict.items():
                            if hasattr(existing_store, key):
                                setattr(existing_store, key, value)
                        self.db.add(existing_store)
                        records_updated += 1
                    else:
                        # Create new store (we need to create Store model first)
                        logger.info(f"Store data: {store_dict}")
                        records_created += 1
                    
                    # Commit every 100 records
                    if records_processed % 100 == 0:
                        self.db.commit()
                        logger.info(f"Processed {records_processed} stores...")
                        
                except Exception as e:
                    logger.error(f"Error processing store {store_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
                    continue
            
            # Final commit
            self.db.commit()
            
            self.update_sync_log(
                sync_log,
                "success",
                records_processed,
                records_created,
                records_updated,
                records_errors,
            )
            return {
                "status": "success",
                "sync_id": sync_log.id,
                "records_processed": records_processed,
                "records_created": records_created,
                "records_updated": records_updated,
                "records_errors": records_errors,
            }

        except Exception as e:
            logger.error(f"Error syncing stores: {e}")
            self.db.rollback()
            self.update_sync_log(
                sync_log,
                "error",
                records_processed,
                records_created,
                records_updated,
                records_errors,
                str(e),
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    def _get_documents_sync(self, doc_type: str, updated_since: Optional[datetime] = None) -> list:
        """Get documents from MoySklad synchronously"""
        all_documents = []
        offset = 0
        limit = 1000

        headers = self.moysklad_connector.headers.copy()
        if 'Content-Type' in headers:
            del headers['Content-Type']

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            if updated_since:
                formatted_date = updated_since.strftime("%Y-%m-%d %H:%M:%S")
                params["filter"] = f"updated>={formatted_date}"

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/{doc_type}",
                        headers=headers,
                        params=params
                    )
                    logger.info(f"API Response Status for {doc_type}: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_documents.extend(rows)
                offset += len(rows)
                time.sleep(0.1)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching {doc_type} at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching {doc_type} at offset {offset}: {e}")
                break

        return all_documents
    
    def _get_stock_sync(self) -> list:
        """Get comprehensive stock from MoySklad synchronously using multiple endpoints"""
        all_stock = []
        
        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }
        
        # Используем подход из рабочего скрипта - множественные endpoints
        stock_endpoints = [
            ("report/stock/all", 1000),  # Comprehensive stock report
            ("report/stock/bystore", 1000),  # Stock by store
            ("report/stock/all/current", 1000)  # Current stock summary
        ]
        
        for endpoint, limit in stock_endpoints:
            offset = 0
            
            try:
                logger.info(f"Fetching stock from {endpoint}")
                
                while True:
                    params = {
                        "limit": limit,
                        "offset": offset
                    }

                    with httpx.Client(timeout=30.0) as client:
                        response = client.get(
                            f"{self.moysklad_connector.base_url}/{endpoint}",
                            headers=headers,
                            params=params
                        )
                        
                        # Обработка rate limiting (429)
                        if response.status_code == 429:
                            retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                            logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                            time.sleep(retry_after / 1000)
                            continue
                        
                        logger.info(f"API Response Status for {endpoint}: {response.status_code}")
                        
                        response.raise_for_status()
                        data = response.json()
                        
                    # Handle different response formats
                    rows = data.get("rows", []) if isinstance(data, dict) else data if isinstance(data, list) else []
                    if not rows:
                        break

                    all_stock.extend(rows)
                    offset += len(rows)
                    
                    # Улучшенный rate limiting как в рабочем скрипте
                    time.sleep(0.02)
                    
                    # Проверяем наличие следующих страниц
                    meta = data.get("meta", {})
                    if offset >= meta.get("size", 0):
                        break
                        
                    # Prevent infinite loops
                    if offset > 10000:
                        break
                        
            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching stock from {endpoint} at offset {offset}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error fetching stock from {endpoint} at offset {offset}: {e}")
                continue

        return all_stock
    
    def _get_stores_sync(self) -> list:
        """Get stores from MoySklad synchronously"""
        all_stores = []
        offset = 0
        limit = 1000

        headers = self.moysklad_connector.headers.copy()
        if 'Content-Type' in headers:
            del headers['Content-Type']

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/store",
                        headers=headers,
                        params=params
                    )
                    logger.info(f"API Response Status for stores: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_stores.extend(rows)
                offset += len(rows)
                time.sleep(0.1)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching stores at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching stores at offset {offset}: {e}")
                break

        return all_stores
    
    def _get_currencies_sync(self) -> list:
        """Get currencies from MoySklad synchronously"""
        all_currencies = []
        offset = 0
        limit = 1000

        headers = self.moysklad_connector.headers.copy()
        if 'Content-Type' in headers:
            del headers['Content-Type']

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/currency",
                        headers=headers,
                        params=params
                    )
                    logger.info(f"API Response Status for currencies: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_currencies.extend(rows)
                offset += len(rows)
                time.sleep(0.1)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching currencies at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching currencies at offset {offset}: {e}")
                break

        return all_currencies
    
    def _get_product_groups_sync(self) -> list:
        """Get product groups from MoySklad synchronously"""
        all_groups = []
        offset = 0
        limit = 1000

        headers = self.moysklad_connector.headers.copy()
        if 'Content-Type' in headers:
            del headers['Content-Type']

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/productfolder",
                        headers=headers,
                        params=params
                    )
                    logger.info(f"API Response Status for product groups: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_groups.extend(rows)
                offset += len(rows)
                time.sleep(0.1)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching product groups at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching product groups at offset {offset}: {e}")
                break

        return all_groups
    
    def _get_services_sync(self) -> list:
        """Get services from MoySklad synchronously"""
        all_services = []
        offset = 0
        limit = 1000

        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/service",
                        headers=headers,
                        params=params
                    )
                    
                    # Обработка rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                        logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                        time.sleep(retry_after / 1000)
                        continue
                    
                    logger.info(f"API Response Status for services: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_services.extend(rows)
                offset += len(rows)
                time.sleep(0.02)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching services at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching services at offset {offset}: {e}")
                break

        return all_services
    
    def _get_bundles_sync(self) -> list:
        """Get bundles from MoySklad synchronously"""
        all_bundles = []
        offset = 0
        limit = 1000

        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/bundle",
                        headers=headers,
                        params=params
                    )
                    
                    # Обработка rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                        logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                        time.sleep(retry_after / 1000)
                        continue
                    
                    logger.info(f"API Response Status for bundles: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_bundles.extend(rows)
                offset += len(rows)
                time.sleep(0.02)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching bundles at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching bundles at offset {offset}: {e}")
                break

        return all_bundles
    
    def _get_variants_sync(self) -> list:
        """Get variants from MoySklad synchronously"""
        all_variants = []
        offset = 0
        limit = 1000

        headers = {
            "Authorization": f"Bearer {self.moysklad_connector.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        }

        while True:
            params = {
                "limit": limit,
                "offset": offset
            }

            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(
                        f"{self.moysklad_connector.base_url}/entity/variant",
                        headers=headers,
                        params=params
                    )
                    
                    # Обработка rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                        logger.warning(f"Rate limit 429. Ожидаем {retry_after/1000} секунд")
                        time.sleep(retry_after / 1000)
                        continue
                    
                    logger.info(f"API Response Status for variants: {response.status_code}")
                    
                    response.raise_for_status()
                    data = response.json()
                    
                rows = data.get("rows", [])
                if not rows:
                    break

                all_variants.extend(rows)
                offset += len(rows)
                time.sleep(0.02)

            except httpx.HTTPStatusError as e:
                logger.error(f"Error fetching variants at offset {offset}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error fetching variants at offset {offset}: {e}")
                break

        return all_variants
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse datetime string from MoySklad"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return None
    
    def _parse_decimal(self, value) -> float:
        """Parse decimal value from MoySklad"""
        if value is None or value == "":
            return 0.0
        try:
            return float(value)
        except:
            return 0.0
    
    def _get_customer_id_by_external_id(self, external_id: str) -> Optional[int]:
        """Get customer ID by external ID"""
        if not external_id:
            return None
        try:
            customer = self.db.execute(
                text("SELECT id FROM customers WHERE external_id = :external_id"),
                {"external_id": external_id},
            ).scalar_one_or_none()
            return customer.id if customer else None
        except:
            return None
