"""
Store endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.schemas.store import Store

router = APIRouter()


@router.get("/", response_model=List[Store])
async def get_stores(
    db: AsyncSession = Depends(get_db)
):
    """Get all stores"""
    try:
        result = await db.execute(text("SELECT * FROM stores ORDER BY name"))
        stores_data = result.fetchall()
        
        # Convert to dict format
        stores_list = []
        for row in stores_data:
            stores_list.append({
                "id": row.id,
                "external_id": row.external_id,
                "name": row.name,
                "code": row.code,
                "address": row.address,
                "archived": row.archived,
                "created_at": row.created_at,
                "updated_at": row.updated_at
            })
        
        return stores_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stores: {str(e)}")
