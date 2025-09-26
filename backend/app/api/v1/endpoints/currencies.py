"""
Currency endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.schemas.currency import Currency

router = APIRouter()


@router.get("/", response_model=List[Currency])
async def get_currencies(
    db: AsyncSession = Depends(get_db)
):
    """Get all currencies"""
    try:
        result = await db.execute(text("SELECT * FROM currencies ORDER BY name"))
        currencies_data = result.fetchall()
        
        # Convert to dict format
        currencies_list = []
        for row in currencies_data:
            currencies_list.append({
                "id": row.id,
                "external_id": row.external_id,
                "name": row.name,
                "code": row.code,
                "full_name": row.full_name,
                "rate": float(row.rate or 1.0),
                "indirect": getattr(row, 'indirect', False),
                "archived": getattr(row, 'archived', False),
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return currencies_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching currencies: {str(e)}")
