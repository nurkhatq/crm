"""
Analytics endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, outerjoin, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.redis import get_cache_service, CacheService
from app.models import Product, StockReport as ProductStock, Customer
from app.schemas.analytics import KPIMetrics, TopProducts, TopProduct, ProductForecast, ForecastPoint

router = APIRouter()


@router.get("/kpi", response_model=KPIMetrics)
async def get_kpi_metrics(
    db: AsyncSession = Depends(get_db),
    redis: CacheService = Depends(get_cache_service)
):
    """Get KPI metrics"""
    
    # Try to get from cache first
    cache_key = "kpi_metrics"
    cached_metrics = await redis.get(cache_key)
    if cached_metrics:
        return KPIMetrics(**cached_metrics)
    
    # Calculate metrics
    # Total products
    products_result = await db.execute(select(func.count(Product.id)))
    total_products = products_result.scalar()
    
    # Total customers
    customers_result = await db.execute(select(func.count(Customer.id)))
    total_customers = customers_result.scalar()
    
    # Total documents - simplified for now
    total_documents = 0
    
    # Total revenue - simplified for now
    total_revenue = Decimal("0")
    
    # Total stock value - simplified for now
    total_stock_value = Decimal("0")
    
    # Get the main currency - simplified for now
    main_currency = "ТЕН"
    
    # Low stock products - simplified for now
    low_stock_products = 0
    
    # Last sync time - simplified for now
    last_sync = None
    
    metrics = KPIMetrics(
        total_products=total_products,
        total_customers=total_customers,
        total_documents=total_documents,
        total_revenue=total_revenue,
        total_stock_value=total_stock_value,
        low_stock_products=low_stock_products,
        last_sync=last_sync,
        currency=main_currency
    )
    
    # Cache for 5 minutes
    await redis.set(cache_key, metrics.dict(), ttl=300)
    
    return metrics


@router.get("/products/top", response_model=TopProducts)
async def get_top_products(
    limit: int = Query(5, ge=1, le=20, description="Number of top products to return"),
    period_days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: AsyncSession = Depends(get_db),
    redis: CacheService = Depends(get_cache_service)
):
    """Get top products by sales"""
    
    cache_key = f"top_products_{limit}_{period_days}"
    cached_result = await redis.get(cache_key)
    if cached_result:
        return TopProducts(**cached_result)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    # Get top products by stock quantity (simplified approach since we don't have sales data)
    query = select(
        Product.id,
        Product.name,
        Product.code,
        Product.article,
        func.coalesce(ProductStock.stock, 0).label('stock'),
        case(
            (Product.sale_price > 0, Product.sale_price),
            (Product.buy_price > 0, Product.buy_price),
            else_=0
        ).label('price')
    ).select_from(
        Product
    ).outerjoin(
        ProductStock, Product.id == ProductStock.product_id
    ).where(
        ProductStock.stock > 0  # Only products with stock
    ).order_by(
        desc(func.coalesce(ProductStock.stock, 0))  # Order by stock quantity
    ).limit(limit)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    top_products = [
        TopProduct(
            product_id=row.id,
            product_name=row.name,
            sales_count=0,  # No sales data available
            revenue=Decimal(str(row.price)),  # Show buy price instead of stock value
            stock=Decimal(str(row.stock))
        )
        for row in rows
    ]
    
    response = TopProducts(
        products=top_products,
        period="по количеству остатков"
    )
    
    # Cache for 10 minutes
    await redis.set(cache_key, response.dict(), ttl=600)
    
    return response


@router.get("/products/{product_id}/forecast", response_model=ProductForecast)
async def get_product_forecast(
    product_id: int,
    days: int = Query(30, ge=7, le=90, description="Forecast period in days"),
    db: AsyncSession = Depends(get_db),
    redis: CacheService = Depends(get_cache_service)
):
    """Get product sales forecast using simple moving average"""
    
    cache_key = f"product_forecast_{product_id}_{days}"
    cached_result = await redis.get(cache_key)
    if cached_result:
        return ProductForecast(**cached_result)
    
    # Get product
    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get historical sales data (simplified - using document count as proxy)
    # In real scenario, you'd need to join with document positions
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Use 90 days of history
    
    # This is a simplified calculation
    # In reality, you'd need to get actual sales quantities from document positions
    historical_data = []
    for i in range(90):
        date = start_date + timedelta(days=i)
        # Simulate some sales data (in real scenario, get from document positions)
        sales = 0  # Placeholder
        historical_data.append(sales)
    
    # Simple moving average forecast
    window_size = 7
    if len(historical_data) >= window_size:
        recent_avg = sum(historical_data[-window_size:]) / window_size
    else:
        recent_avg = sum(historical_data) / len(historical_data) if historical_data else 0
    
    # Generate forecast points
    forecast_points = []
    for i in range(days):
        forecast_date = end_date + timedelta(days=i+1)
        # Add some random variation to the forecast
        import random
        variation = random.uniform(0.8, 1.2)
        predicted_sales = Decimal(str(recent_avg * variation))
        
        forecast_points.append(ForecastPoint(
            date=forecast_date,
            predicted_sales=predicted_sales,
            confidence_lower=predicted_sales * Decimal('0.8'),
            confidence_upper=predicted_sales * Decimal('1.2')
        ))
    
    forecast = ProductForecast(
        product_id=product.id,
        product_name=product.name,
        forecast_points=forecast_points,
        method="simple_moving_average",
        accuracy=Decimal('0.75')  # Placeholder accuracy
    )
    
    # Cache for 1 hour
    await redis.set(cache_key, forecast.dict(), ttl=3600)
    
    return forecast
