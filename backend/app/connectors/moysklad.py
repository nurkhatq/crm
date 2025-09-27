"""
MoySklad API connector с улучшенным парсингом и обработкой ошибок
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)


class MoySkladError(Exception):
    """Base exception for MoySklad connector"""
    pass


class AuthenticationError(MoySkladError):
    """Authentication error"""
    pass


class RateLimitError(MoySkladError):
    """Rate limit exceeded error"""
    pass


class APIError(MoySkladError):
    """General API error"""
    pass


class RateLimiter:
    """Improved rate limiter for MoySklad API"""
    
    def __init__(self, requests_per_second: int = 5):
        self.requests_per_second = requests_per_second
        self.last_request_time = 0
        self.request_interval = 1.0 / requests_per_second
    
    async def wait_if_needed(self):
        """Wait if needed to respect rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_interval:
            wait_time = self.request_interval - time_since_last
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()


class MoySkladConnector:
    """Улучшенный MoySklad API connector для read-only операций"""
    
    def __init__(self):
        self.base_url = "https://api.moysklad.ru/api/remap/1.2/"
        self.token = settings.MOYSKLAD_TOKEN
        self.rate_limiter = RateLimiter(requests_per_second=5)
        self.session_timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Проверка токена
        if not self.token or self.token == "your_moysklad_token_here":
            logger.warning("MoySklad token not configured. Sync operations will be disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("MoySklad connector initialized successfully")
        
        # Настройка заголовков
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept-Encoding": "gzip",
            "Accept": "application/json;charset=utf-8",
            "User-Agent": "CRM-MoySklad/2.0",
            "Cache-Control": "no-cache"
        } if self.enabled else {}
    
    def is_enabled(self) -> bool:
        """Проверить, активен ли коннектор"""
        return self.enabled and self.token and self.token != "your_moysklad_token_here"
    
    async def test_connection(self) -> bool:
        """Тест соединения с API МойСклад"""
        if not self.is_enabled():
            logger.warning("Connector is not enabled")
            return False
        
        try:
            # Тестируем простейший запрос
            data, status_code = await self._make_request("GET", "entity/product", params={"limit": 1})
            
            if status_code == 200 and isinstance(data, dict):
                logger.info(f"✅ Подключение к МойСклад успешно. Найдено товаров: {data.get('meta', {}).get('size', 0)}")
                return True
            else:
                logger.error(f"❌ Неожиданный ответ API: {status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к МойСклад API: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, RateLimitError))
    )
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Выполнить HTTP запрос к API МойСклад с retry логикой"""
        
        if not self.is_enabled():
            raise APIError("MoySklad connector is not enabled")
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        # Подготовка URL
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        # Подготовка заголовков
        headers = self.headers.copy()
        if method.upper() in ['POST', 'PUT', 'PATCH'] and json_data:
            headers['Content-Type'] = 'application/json'
        
        logger.debug(f"🔄 {method} {endpoint} | Params: {params}")
        
        try:
            async with httpx.AsyncClient(timeout=self.session_timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params or {},
                    json=json_data
                )
                
                # Обработка различных HTTP статусов
                if response.status_code == 200:
                    try:
                        data = response.json()
                        return data, response.status_code
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Ошибка парсинга JSON: {e}")
                        raise APIError(f"Invalid JSON response: {e}")
                
                elif response.status_code == 401:
                    logger.error("❌ Ошибка аутентификации - неверный токен")
                    raise AuthenticationError("Invalid or expired token")
                
                elif response.status_code == 403:
                    logger.error("❌ Доступ запрещен - недостаточно прав")
                    raise AuthenticationError("Insufficient permissions")
                
                elif response.status_code == 429:
                    # Rate limiting
                    retry_after = int(response.headers.get('X-Lognex-Retry-After', 5000))
                    logger.warning(f"⚠️ Rate limit exceeded. Waiting {retry_after}ms")
                    await asyncio.sleep(retry_after / 1000)
                    raise RateLimitError("Rate limit exceeded")
                
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Endpoint not found: {endpoint}")
                    return {"rows": [], "meta": {"size": 0}}, 404
                
                elif response.status_code >= 500:
                    logger.error(f"❌ Серверная ошибка МойСклад: {response.status_code}")
                    raise APIError(f"Server error: {response.status_code}")
                
                else:
                    # Другие ошибки
                    logger.error(f"❌ Неожиданный статус: {response.status_code}, Ответ: {response.text}")
                    raise APIError(f"Unexpected status code: {response.status_code}")
                    
        except httpx.TimeoutException:
            logger.error("❌ Timeout при запросе к API")
            raise APIError("Request timeout")
        
        except httpx.ConnectError as e:
            logger.error(f"❌ Ошибка соединения: {e}")
            raise APIError(f"Connection error: {e}")
        
        except Exception as e:
            if isinstance(e, (AuthenticationError, RateLimitError, APIError)):
                raise
            logger.error(f"❌ Неожиданная ошибка: {e}")
            raise APIError(f"Unexpected error: {e}")
    
    def _safe_extract_value(self, data: Dict, path: str, default: Any = None) -> Any:
        """Безопасное извлечение значения по пути в словаре"""
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
    
    async def get_all_entities(
        self, 
        entity_type: str, 
        expand: Optional[str] = None,
        filters: Optional[str] = None,
        limit_per_request: int = 1000
    ) -> List[Dict[str, Any]]:
        """Получить все сущности с пагинацией"""
        
        if not self.is_enabled():
            logger.warning("Connector is not enabled")
            return []
        
        all_data = []
        offset = 0
        
        # Уменьшаем размер batch при использовании expand
        if expand:
            limit_per_request = min(limit_per_request, 100)
        
        logger.info(f"📥 Начинаем загрузку {entity_type} (expand: {expand})")
        
        while True:
            params = {
                'offset': offset, 
                'limit': limit_per_request
            }
            
            if expand:
                params['expand'] = expand
            if filters:
                params['filter'] = filters
            
            try:
                data, status_code = await self._make_request('GET', f'entity/{entity_type}', params=params)
                
                if status_code == 404:
                    logger.warning(f"⚠️ Entity type '{entity_type}' not found")
                    break
                
                rows = data.get('rows', [])
                if not rows:
                    logger.info(f"✅ Загрузка {entity_type} завершена - нет больше данных")
                    break
                
                all_data.extend(rows)
                offset += len(rows)
                
                # Логирование прогресса
                if offset % 1000 == 0 or offset <= 1000:
                    logger.info(f"📊 {entity_type}: загружено {offset} записей...")
                
                # Проверяем, есть ли еще данные
                meta = data.get('meta', {})
                total_size = meta.get('size', 0)
                
                if offset >= total_size:
                    logger.info(f"✅ Загрузка {entity_type} завершена - достигнут конец ({total_size})")
                    break
                
                # Небольшая пауза между запросами
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при загрузке {entity_type} (offset: {offset}): {e}")
                break
        
        logger.info(f"✅ Загружено {len(all_data)} записей {entity_type}")
        return all_data
    
    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Получить все товары с расширенной информацией"""
        expand_fields = "owner,group,uom,supplier,buyPrice.currency,salePrices.currency,images,attributes"
        products = await self.get_all_entities('product', expand=expand_fields)
        
        # Дополнительно загружаем услуги и комплекты
        try:
            services = await self.get_all_entities('service', expand=expand_fields)
            bundles = await self.get_all_entities('bundle', expand=expand_fields)
            
            # Помечаем тип для различения
            for product in products:
                product['entity_type'] = 'product'
            for service in services:
                service['entity_type'] = 'service'
            for bundle in bundles:
                bundle['entity_type'] = 'bundle'
            
            all_items = products + services + bundles
            logger.info(f"📦 Загружено товаров: {len(products)}, услуг: {len(services)}, комплектов: {len(bundles)}")
            
            return all_items
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки дополнительных типов товаров: {e}")
            return products
    
    async def get_all_customers(self) -> List[Dict[str, Any]]:
        """Получить всех контрагентов"""
        expand_fields = "owner,group,state,tags,priceType"
        return await self.get_all_entities('counterparty', expand=expand_fields)
    
    async def get_all_documents(self, document_type: str) -> List[Dict[str, Any]]:
        """Получить документы определенного типа"""
        expand_fields = "agent,organization,owner,state,positions.assortment"
        return await self.get_all_entities(document_type, expand=expand_fields)
    
    async def get_all_stores(self) -> List[Dict[str, Any]]:
        """Получить все склады"""
        return await self.get_all_entities('store')
    
    async def get_stock_report(self) -> List[Dict[str, Any]]:
        """Получить отчет об остатках"""
        try:
            data, status_code = await self._make_request('GET', 'report/stock/all')
            
            if status_code == 200 and isinstance(data, dict):
                return data.get('rows', [])
            else:
                logger.warning(f"⚠️ Не удалось получить отчет об остатках: {status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения отчета об остатках: {e}")
            return []
    
    async def get_turnover_report(self, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить отчет по оборотам товаров"""
        try:
            params = {}
            if filters:
                params['filter'] = filters
            
            data, status_code = await self._make_request('GET', 'report/turnover/all', params=params)
            
            if status_code == 200 and isinstance(data, dict):
                return data.get('rows', [])
            else:
                logger.warning(f"⚠️ Не удалось получить отчет по оборотам: {status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения отчета по оборотам: {e}")
            return []
    
    async def get_profit_report(self) -> List[Dict[str, Any]]:
        """Получить отчет по прибыльности"""
        try:
            data, status_code = await self._make_request('GET', 'report/profit/byproduct')
            
            if status_code == 200 and isinstance(data, dict):
                return data.get('rows', [])
            else:
                logger.warning(f"⚠️ Не удалось получить отчет по прибыльности: {status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения отчета по прибыльности: {e}")
            return []


# Глобальный экземпляр коннектора
moysklad_connector = MoySkladConnector()