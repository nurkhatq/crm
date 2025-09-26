"""
Employee endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.employee import Employee
from app.schemas.employee import Employee as EmployeeSchema

router = APIRouter()


@router.get("/", response_model=List[EmployeeSchema])
async def get_employees(
    db: AsyncSession = Depends(get_db)
):
    """Get all employees"""
    try:
        result = await db.execute(select(Employee))
        employees = result.scalars().all()
        return employees
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")
