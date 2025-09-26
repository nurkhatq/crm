"""
Product endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Product, ProductStock as ProductStockModel
from app.schemas.product import Product as ProductSchema, ProductWithStock, ProductStock, ProductStockWithProduct
from app.core.redis import get_redis, CacheService

router = APIRouter()


@router.get("/", response_model=List[ProductWithStock])
async def get_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for product name"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    db: AsyncSession = Depends(get_db)
):
    """Get products with optional filtering"""
    
    # Build query
    query = select(Product).options(selectinload(Product.stock))
    
    # Apply filters
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    
    if archived is not None:
        query = query.where(Product.archived == archived)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products


@router.get("/{product_id}", response_model=ProductWithStock)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product by ID"""
    
    query = select(Product).options(selectinload(Product.stock)).where(Product.id == product_id)
    result = await db.execute(query)
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.get("/{product_id}/stock", response_model=ProductStock)
async def get_product_stock(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get product stock information"""
    
    query = select(ProductStockModel).where(ProductStockModel.product_id == product_id)
    result = await db.execute(query)
    stock = result.scalar_one_or_none()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Product stock not found")
    
    return stock


@router.get("/export/csv")
async def export_products_csv(
    search: Optional[str] = Query(None, description="Search term for product name"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    db: AsyncSession = Depends(get_db)
):
    """Export products to CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Build query
    query = select(Product).options(selectinload(Product.stock))
    
    # Apply filters
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    
    if archived is not None:
        query = query.where(Product.archived == archived)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Name", "Code", "Article", "Description", "Archived",
        "Buy Price", "Sale Price", "Currency", "UOM", "Group", "Supplier",
        "Stock", "Reserve", "Available", "Store"
    ])
    
    # Write data
    for product in products:
        stock = product.stock
        writer.writerow([
            product.id,
            product.name,
            product.code or "",
            product.article or "",
            product.description or "",
            product.archived,
            product.buy_price or 0,
            product.sale_price or 0,
            product.currency,
            product.uom or "",
            product.group_name or "",
            product.supplier_name or "",
            stock.stock if stock else 0,
            stock.reserve if stock else 0,
            stock.available if stock else 0,
            stock.store_name if stock else ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products.csv"}
    )


@router.get("/stock/", response_model=List[ProductStockWithProduct])
async def get_product_stock(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    store_name: Optional[str] = Query(None, description="Filter by store name"),
    min_stock: Optional[float] = Query(None, description="Minimum stock level"),
    db: AsyncSession = Depends(get_db)
):
    """Get product stock information"""
    
    # Build query with product information
    query = select(ProductStockModel, Product).join(Product, ProductStockModel.product_id == Product.id)
    
    # Apply filters
    if store_name:
        query = query.where(ProductStockModel.store_name.ilike(f"%{store_name}%"))
    
    if min_stock is not None:
        query = query.where(ProductStockModel.stock >= min_stock)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    rows = result.all()
    
    # Build response with product information
    stock_records = []
    for stock_row, product_row in rows:
        # Create product schema
        product_schema = ProductSchema(
            id=product_row.id,
            name=product_row.name,
            code=product_row.code,
            article=product_row.article,
            description=product_row.description,
            archived=product_row.archived,
            buy_price=product_row.buy_price,
            sale_price=product_row.sale_price,
            currency=product_row.currency,
            uom=product_row.uom,
            group_name=product_row.group_name,
            supplier_name=product_row.supplier_name,
            external_id=product_row.external_id,
            external_updated=product_row.external_updated,
            created_at=product_row.created_at,
            updated_at=product_row.updated_at
        )
        
        # Create stock schema with product
        stock_schema = ProductStockWithProduct(
            id=stock_row.id,
            product_id=stock_row.product_id,
            stock=stock_row.stock,
            reserve=stock_row.reserve,
            in_transit=stock_row.in_transit,
            available=stock_row.available,
            store_name=stock_row.store_name,
            store_id=stock_row.store_id,
            created_at=stock_row.created_at,
            updated_at=stock_row.updated_at,
            product=product_schema
        )
        stock_records.append(stock_schema)
    
    return stock_records


@router.get("/stock/low-stock", response_model=List[ProductWithStock])
async def get_low_stock_products(
    threshold: float = Query(10.0, ge=0, description="Low stock threshold"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get products with low stock levels"""
    
    # Build query for products with low stock
    query = select(Product).options(selectinload(Product.stock)).outerjoin(
        ProductStockModel, Product.id == ProductStockModel.product_id
    ).where(
        func.coalesce(ProductStockModel.stock, 0) <= threshold
    ).distinct()
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products
