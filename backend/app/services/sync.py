"""
Synchronization service for MoySklad data
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.moysklad import moysklad_connector
from app.models import Product, ProductStock, Customer, Document, SyncLog
from app.schemas.sync import SyncLog as SyncLogSchema

logger = logging.getLogger(__name__)


class SyncService:
    """Service for synchronizing data from MoySklad"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_sync_log(
        self, 
        sync_type: str, 
        entity_type: Optional[str] = None
    ) -> SyncLog:
        """Create sync log entry"""
        sync_log = SyncLog(
            sync_type=sync_type,
            entity_type=entity_type,
            status="in_progress",
            started_at=datetime.now(timezone.utc)
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
        error_message: Optional[str] = None,
        error_details: Optional[str] = None
    ) -> None:
        """Update sync log entry"""
        sync_log.status = status
        sync_log.records_processed = records_processed
        sync_log.records_created = records_created
        sync_log.records_updated = records_updated
        sync_log.records_errors = records_errors
        sync_log.error_message = error_message
        sync_log.error_details = error_details
        
        if status in ["success", "error"]:
            sync_log.completed_at = datetime.now(timezone.utc)
        
        await self.db.commit()
    
    async def sync_products(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize products from MoySklad"""
        if not moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("products", "product")
        
        try:
            # Initialize counters
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Get last sync time for incremental sync
            last_sync = None
            if not force:
                last_sync_log = await self.db.execute(
                    select(SyncLog)
                    .where(SyncLog.sync_type == "products")
                    .where(SyncLog.status == "success")
                    .order_by(SyncLog.completed_at.desc())
                    .limit(1)  # Only get the most recent one
                )
                last_sync_result = last_sync_log.scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at
            
            # Fetch products from MoySklad
            products_data = await moysklad_connector.get_all_products(updated_since=last_sync)
            
            for product_data in products_data:
                try:
                    records_processed += 1
                    
                    # Check if product exists
                    existing_product = await self.db.execute(
                        select(Product).where(Product.external_id == product_data["id"])
                    )
                    existing_product = existing_product.scalar_one_or_none()
                    
                    # Prepare product data
                    product_dict = {
                        "external_id": product_data["id"],
                        "name": product_data.get("name", ""),
                        "code": product_data.get("code"),
                        "article": product_data.get("article"),
                        "description": product_data.get("description"),
                        "archived": product_data.get("archived", False),
                        "external_raw": json.dumps(product_data, ensure_ascii=False),
                        "external_updated": datetime.fromisoformat(
                            product_data.get("updated", "").replace("Z", "+00:00")
                        ) if product_data.get("updated") else None
                    }
                    
                    # Extract pricing information
                    if "salePrices" in product_data and product_data["salePrices"]:
                        product_dict["sale_price"] = Decimal(str(product_data["salePrices"][0].get("value", 0)))
                    
                    if "buyPrice" in product_data and product_data["buyPrice"]:
                        product_dict["buy_price"] = Decimal(str(product_data["buyPrice"].get("value", 0)))
                    
                    # Extract additional information
                    if "uom" in product_data and product_data["uom"]:
                        product_dict["uom"] = product_data["uom"].get("name")
                    
                    if "productFolder" in product_data and product_data["productFolder"]:
                        product_dict["group_name"] = product_data["productFolder"].get("name")
                    
                    if "supplier" in product_data and product_data["supplier"]:
                        product_dict["supplier_name"] = product_data["supplier"].get("name")
                    
                    if existing_product:
                        # Update existing product
                        for key, value in product_dict.items():
                            setattr(existing_product, key, value)
                        records_updated += 1
                    else:
                        # Create new product
                        new_product = Product(**product_dict)
                        self.db.add(new_product)
                        records_created += 1
                    
                except Exception as e:
                    logger.error(f"Error processing product {product_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
            
            await self.db.commit()
            await self.update_sync_log(
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
            await self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    async def sync_customers(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize customers from MoySklad"""
        if not moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("customers", "counterparty")
        
        try:
            # Initialize counters
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Get last sync time for incremental sync
            last_sync = None
            if not force:
                last_sync_log = await self.db.execute(
                    select(SyncLog)
                    .where(SyncLog.sync_type == "customers")
                    .where(SyncLog.status == "success")
                    .order_by(SyncLog.completed_at.desc())
                    .limit(1)  # Only get the most recent one
                )
                last_sync_result = last_sync_log.scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at
            
            # Fetch customers from MoySklad
            customers_data = await moysklad_connector.get_all_customers(updated_since=last_sync)
            
            for customer_data in customers_data:
                try:
                    records_processed += 1
                    
                    # Check if customer exists
                    existing_customer = await self.db.execute(
                        select(Customer).where(Customer.external_id == customer_data["id"])
                    )
                    existing_customer = existing_customer.scalar_one_or_none()
                    
                    # Prepare customer data
                    customer_dict = {
                        "external_id": customer_data["id"],
                        "name": customer_data.get("name", ""),
                        "code": customer_data.get("code"),
                        "legal_title": customer_data.get("legalTitle"),
                        "email": customer_data.get("email"),
                        "phone": customer_data.get("phone"),
                        "inn": customer_data.get("inn"),
                        "kpp": customer_data.get("kpp"),
                        "archived": customer_data.get("archived", False),
                        "external_raw": json.dumps(customer_data, ensure_ascii=False),
                        "external_updated": datetime.fromisoformat(
                            customer_data.get("updated", "").replace("Z", "+00:00")
                        ) if customer_data.get("updated") else None
                    }
                    
                    # Extract address information
                    if "actualAddress" in customer_data and customer_data["actualAddress"]:
                        address_parts = []
                        for field in ["addInfo", "apartment", "city", "comment", "country", "house", "postalCode", "region", "street"]:
                            if customer_data["actualAddress"].get(field):
                                address_parts.append(customer_data["actualAddress"][field])
                        customer_dict["address"] = ", ".join(address_parts)
                    
                    if existing_customer:
                        # Update existing customer
                        for key, value in customer_dict.items():
                            setattr(existing_customer, key, value)
                        records_updated += 1
                    else:
                        # Create new customer
                        new_customer = Customer(**customer_dict)
                        self.db.add(new_customer)
                        records_created += 1
                    
                except Exception as e:
                    logger.error(f"Error processing customer {customer_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
            
            await self.db.commit()
            await self.update_sync_log(
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
            await self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    async def sync_documents(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize documents from MoySklad"""
        if not moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("documents", "document")
        
        try:
            # Initialize counters
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            # Document types to sync
            document_types = ["customerorder", "demand", "invoiceout", "salesreturn", "retailsale"]
            
            # Get last sync time for incremental sync
            last_sync = None
            if not force:
                last_sync_log = await self.db.execute(
                    select(SyncLog)
                    .where(SyncLog.sync_type == "documents")
                    .where(SyncLog.status == "success")
                    .order_by(SyncLog.completed_at.desc())
                    .limit(1)  # Only get the most recent one
                )
                last_sync_result = last_sync_log.scalar_one_or_none()
                if last_sync_result:
                    last_sync = last_sync_result.completed_at
            
            # Fetch documents from MoySklad
            documents_data = await moysklad_connector.get_all_documents(
                document_types, 
                updated_since=last_sync
            )
            
            for document_data in documents_data:
                try:
                    records_processed += 1
                    
                    # Check if document exists
                    existing_document = await self.db.execute(
                        select(Document).where(Document.external_id == document_data["id"])
                    )
                    existing_document = existing_document.scalar_one_or_none()
                    
                    # Prepare document data
                    document_dict = {
                        "external_id": document_data["id"],
                        "name": document_data.get("name", ""),
                        "document_type": document_data.get("_document_type", ""),
                        "applicable": document_data.get("applicable", False),
                        "external_raw": json.dumps(document_data, ensure_ascii=False),
                        "external_updated": datetime.fromisoformat(
                            document_data.get("updated", "").replace("Z", "+00:00")
                        ) if document_data.get("updated") else None
                    }
                    
                    # Extract moment
                    if "moment" in document_data and document_data["moment"]:
                        document_dict["moment"] = datetime.fromisoformat(
                            document_data["moment"].replace("Z", "+00:00")
                        )
                    
                    # Extract sum
                    if "sum" in document_data and document_data["sum"]:
                        document_dict["sum"] = Decimal(str(document_data["sum"]))
                    
                    # Extract currency
                    if "rate" in document_data and document_data["rate"]:
                        document_dict["currency"] = document_data["rate"].get("currency", {}).get("name", "RUB")
                    
                    # Extract state
                    if "state" in document_data and document_data["state"]:
                        document_dict["state_name"] = document_data["state"].get("name")
                    
                    # Extract organization
                    if "organization" in document_data and document_data["organization"]:
                        document_dict["organization_name"] = document_data["organization"].get("name")
                    
                    # Extract store
                    if "store" in document_data and document_data["store"]:
                        document_dict["store_name"] = document_data["store"].get("name")
                    
                    # Extract customer
                    customer_id = None
                    if "agent" in document_data and document_data["agent"]:
                        customer_external_id = document_data["agent"]["id"]
                        customer = await self.db.execute(
                            select(Customer).where(Customer.external_id == customer_external_id)
                        )
                        customer = customer.scalar_one_or_none()
                        if customer:
                            customer_id = customer.id
                    
                    document_dict["customer_id"] = customer_id
                    
                    if existing_document:
                        # Update existing document
                        for key, value in document_dict.items():
                            setattr(existing_document, key, value)
                        records_updated += 1
                    else:
                        # Create new document
                        new_document = Document(**document_dict)
                        self.db.add(new_document)
                        records_created += 1
                    
                except Exception as e:
                    logger.error(f"Error processing document {document_data.get('id', 'unknown')}: {e}")
                    records_errors += 1
            
            await self.db.commit()
            await self.update_sync_log(
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
            logger.error(f"Error syncing documents: {e}")
            await self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    async def sync_stock(self, force: bool = False) -> Dict[str, Any]:
        """Synchronize stock data from MoySklad"""
        if not moysklad_connector.is_enabled():
            return {"error": "MoySklad connector is not enabled"}
        
        sync_log = await self.create_sync_log("stock", "stock")
        
        try:
            # Fetch stock data from MoySklad
            stock_data = await moysklad_connector.get_stock_report()
            
            records_processed = 0
            records_created = 0
            records_updated = 0
            records_errors = 0
            
            for stock_item in stock_data:
                try:
                    records_processed += 1
                    
                    # Find product by external ID
                    product_external_id = stock_item["meta"]["href"].split("/")[-1]
                    product = await self.db.execute(
                        select(Product).where(Product.external_id == product_external_id)
                    )
                    product = product.scalar_one_or_none()
                    
                    if not product:
                        records_errors += 1
                        continue
                    
                    # Check if stock record exists
                    existing_stock = await self.db.execute(
                        select(ProductStock).where(ProductStock.product_id == product.id)
                    )
                    existing_stock = existing_stock.scalar_one_or_none()
                    
                    # Prepare stock data
                    stock_dict = {
                        "product_id": product.id,
                        "stock": Decimal(str(stock_item.get("stock", 0))),
                        "reserve": Decimal(str(stock_item.get("reserve", 0))),
                        "in_transit": Decimal(str(stock_item.get("inTransit", 0))),
                        "available": Decimal(str(stock_item.get("quantity", 0))),
                        "store_name": stock_item.get("name"),
                        "store_id": stock_item.get("id")
                    }
                    
                    if existing_stock:
                        # Update existing stock
                        for key, value in stock_dict.items():
                            setattr(existing_stock, key, value)
                        records_updated += 1
                    else:
                        # Create new stock record
                        new_stock = ProductStock(**stock_dict)
                        self.db.add(new_stock)
                        records_created += 1
                    
                except Exception as e:
                    logger.error(f"Error processing stock item {stock_item.get('id', 'unknown')}: {e}")
                    records_errors += 1
            
            await self.db.commit()
            await self.update_sync_log(
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
            logger.error(f"Error syncing stock: {e}")
            await self.update_sync_log(
                sync_log, 
                "error", 
                records_processed, 
                records_created, 
                records_updated, 
                records_errors,
                str(e)
            )
            return {"error": str(e), "sync_id": sync_log.id}
    
    async def full_sync(self, force: bool = False) -> Dict[str, Any]:
        """Perform full synchronization of all data"""
        results = {}
        
        # Sync products
        results["products"] = await self.sync_products(force)
        
        # Sync customers
        results["customers"] = await self.sync_customers(force)
        
        # Sync documents
        results["documents"] = await self.sync_documents(force)
        
        # Sync stock
        results["stock"] = await self.sync_stock(force)
        
        return results
