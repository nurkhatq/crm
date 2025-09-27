"""
Product turnover endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.schemas.turnover import ProductTurnover
from app.models import ProductTurnover as ProductTurnoverModel

router = APIRouter()


@router.get("/", response_model=List[ProductTurnover])
async def get_product_turnover(
    db: AsyncSession = Depends(get_db)
):
    """Get all product turnover data"""
    try:
        result = await db.execute(select(ProductTurnoverModel))
        turnover_data = result.scalars().all()
        return turnover_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching turnover data: {str(e)}")



