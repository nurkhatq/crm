"""
Product turnover endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.schemas.turnover import ProductTurnover

router = APIRouter()


@router.get("/", response_model=List[ProductTurnover])
async def get_product_turnover(
    db: AsyncSession = Depends(get_db)
):
    """Get all product turnover data"""
    try:
        result = await db.execute(text("SELECT * FROM product_turnover ORDER BY created_at DESC"))
        turnover_data = result.fetchall()
        
        # Convert to dict format
        turnover_list = []
        for row in turnover_data:
            turnover_list.append({
                "id": row.id,
                "product_external_id": row.product_external_id,
                "product_name": row.product_name,
                "product_code": row.product_code,
                "stock_at_period_start": float(row.stock_at_period_start or 0),
                "income": float(row.income or 0),
                "outcome": float(row.outcome or 0),
                "stock_at_period_end": float(row.stock_at_period_end or 0),
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return turnover_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching turnover data: {str(e)}")
