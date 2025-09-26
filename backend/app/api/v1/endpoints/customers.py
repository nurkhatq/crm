"""
Customer endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Customer
from app.schemas.customer import Customer as CustomerSchema

router = APIRouter()


@router.get("/", response_model=List[CustomerSchema])
async def get_customers(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    search: Optional[str] = Query(None, description="Search term for customer name"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    db: AsyncSession = Depends(get_db)
):
    """Get customers with optional filtering"""
    
    # Build query
    query = select(Customer)
    
    # Apply filters
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
    
    if archived is not None:
        query = query.where(Customer.archived == archived)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()
    
    return customers


@router.get("/{customer_id}", response_model=CustomerSchema)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get customer by ID"""
    
    query = select(Customer).where(Customer.id == customer_id)
    result = await db.execute(query)
    customer = result.scalar_one_or_none()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.get("/export/csv")
async def export_customers_csv(
    search: Optional[str] = Query(None, description="Search term for customer name"),
    archived: Optional[bool] = Query(None, description="Filter by archived status"),
    db: AsyncSession = Depends(get_db)
):
    """Export customers to CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Build query
    query = select(Customer)
    
    # Apply filters
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
    
    if archived is not None:
        query = query.where(Customer.archived == archived)
    
    # Execute query
    result = await db.execute(query)
    customers = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Name", "Code", "Legal Title", "Email", "Phone",
        "INN", "KPP", "Address", "Postal Address", "Archived"
    ])
    
    # Write data
    for customer in customers:
        writer.writerow([
            customer.id,
            customer.name,
            customer.code or "",
            customer.legal_title or "",
            customer.email or "",
            customer.phone or "",
            customer.inn or "",
            customer.kpp or "",
            customer.address or "",
            customer.postal_address or "",
            customer.archived
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers.csv"}
    )
