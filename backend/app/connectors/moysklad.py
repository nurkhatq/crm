"""
MoySklad API connector (read-only)
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class MoySkladConnector:
    """MoySklad API connector for read-only operations"""
    
    def __init__(self):
        self.base_url = settings.MOYSKLAD_BASE_URL
        self.token = settings.MOYSKLAD_TOKEN
        self.rate_limit = settings.MOYSKLAD_RATE_LIMIT
        self.batch_size = settings.MOYSKLAD_BATCH_SIZE
        
        if not self.token or self.token == "your_moysklad_token_here":
            logger.warning("MoySklad token not configured. Sync operations will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "MoySkladFullExporter/1.0"
        } if self.enabled else {}
    
    def is_enabled(self) -> bool:
        """Check if connector is enabled"""
        return self.enabled and self.token and self.token != "your_moysklad_token_here"
    
    async def test_connection(self) -> bool:
        """Test connection to MoySklad API"""
        try:
            # Test with products endpoint, limit=1
            data, status = await self._make_request("GET", "entity/product", params={"limit": 1})
            logger.info(f"Подключение успешно. Получено данных: {len(data.get('rows', []))}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к API: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Make HTTP request to MoySklad API with retry logic"""
        if not self.is_enabled():
            raise ValueError("MoySklad connector is not enabled")
        
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Add Content-Type only for POST/PUT requests
        headers = self.headers.copy()
        if method.upper() in ['POST', 'PUT', 'PATCH']:
            headers['Content-Type'] = 'application/json'
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params or {}
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                logger.warning(f"Rate limited. Waiting {retry_after}ms")
                await asyncio.sleep(retry_after / 1000)
                raise httpx.HTTPStatusError("Rate limited", request=response.request, response=response)
            
            # Handle authentication error
            if response.status_code == 401:
                logger.error("Ошибка аутентификации. Проверьте токен")
                raise httpx.HTTPStatusError("Неверный токен", request=response.request, response=response)
            
            # Handle service unavailable
            if response.status_code == 503:
                logger.error(f"MoySklad API service unavailable. Status: {response.status_code}, Response: {response.text}")
                raise httpx.HTTPStatusError("MoySklad API service unavailable", request=response.request, response=response)
            
            response.raise_for_status()
            
            # Parse JSON response
            if response.headers.get('content-type', '').startswith('application/json'):
                return response.json(), response.status_code
            else:
                return {"content": response.text}, response.status_code
    
    async def get_products(
        self, 
        limit: int = 1000, 
        offset: int = 0,
        updated_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get products from MoySklad"""
        if not self.is_enabled():
            return []
        
        params = {
            "limit": min(limit, self.batch_size),
            "offset": offset
        }
        
        if updated_since:
            params["filter"] = f"updated>={updated_since.isoformat()}"
        
        try:
            data, _ = await self._make_request("GET", "entity/product", params)
            return data.get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    async def get_customers(
        self, 
        limit: int = 1000, 
        offset: int = 0,
        updated_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get customers from MoySklad"""
        if not self.is_enabled():
            return []
        
        params = {
            "limit": min(limit, self.batch_size),
            "offset": offset
        }
        
        if updated_since:
            params["filter"] = f"updated>={updated_since.isoformat()}"
        
        try:
            data, _ = await self._make_request("GET", "entity/counterparty", params)
            return data.get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return []
    
    async def get_documents(
        self, 
        document_type: str,
        limit: int = 1000, 
        offset: int = 0,
        updated_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get documents from MoySklad"""
        if not self.is_enabled():
            return []
        
        params = {
            "limit": min(limit, self.batch_size),
            "offset": offset
        }
        
        if updated_since:
            params["filter"] = f"updated>={updated_since.isoformat()}"
        
        try:
            data, _ = await self._make_request("GET", f"entity/{document_type}", params)
            return data.get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching {document_type}: {e}")
            return []
    
    async def get_stock_report(self) -> List[Dict[str, Any]]:
        """Get stock report from MoySklad"""
        if not self.is_enabled():
            return []
        
        try:
            data, _ = await self._make_request("GET", "report/stock/all", {"limit": 1000})
            return data.get("rows", [])
        except Exception as e:
            logger.error(f"Error fetching stock report: {e}")
            return []
    
    async def get_all_products(self, updated_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all products with pagination"""
        all_products = []
        offset = 0
        
        while True:
            products = await self.get_products(
                limit=self.batch_size,
                offset=offset,
                updated_since=updated_since
            )
            
            if not products:
                break
                
            all_products.extend(products)
            offset += len(products)
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        return all_products
    
    async def get_all_customers(self, updated_since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get all customers with pagination"""
        all_customers = []
        offset = 0
        
        while True:
            customers = await self.get_customers(
                limit=self.batch_size,
                offset=offset,
                updated_since=updated_since
            )
            
            if not customers:
                break
                
            all_customers.extend(customers)
            offset += len(customers)
            
            # Rate limiting
            await asyncio.sleep(0.1)
        
        return all_customers
    
    async def get_all_documents(
        self, 
        document_types: List[str],
        updated_since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get all documents of specified types with pagination"""
        all_documents = []
        
        for doc_type in document_types:
            offset = 0
            
            while True:
                documents = await self.get_documents(
                    document_type=doc_type,
                    limit=self.batch_size,
                    offset=offset,
                    updated_since=updated_since
                )
                
                if not documents:
                    break
                    
                # Add document type to each document
                for doc in documents:
                    doc["_document_type"] = doc_type
                
                all_documents.extend(documents)
                offset += len(documents)
                
                # Rate limiting
                await asyncio.sleep(0.1)
        
        return all_documents


# Global connector instance
moysklad_connector = MoySkladConnector()
