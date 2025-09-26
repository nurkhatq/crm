"""
Document endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Document
from app.schemas.document import Document as DocumentSchema

router = APIRouter()


@router.get("/", response_model=List[DocumentSchema])
async def get_documents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    applicable: Optional[bool] = Query(None, description="Filter by applicable status"),
    db: AsyncSession = Depends(get_db)
):
    """Get documents with optional filtering"""
    
    # Build query
    query = select(Document)
    
    # Apply filters
    if document_type:
        query = query.where(Document.document_type == document_type)
    
    if customer_id:
        query = query.where(Document.customer_id == customer_id)
    
    if applicable is not None:
        query = query.where(Document.applicable == applicable)
    
    # Order by moment descending
    query = query.order_by(desc(Document.moment))
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return documents


@router.get("/{document_id}", response_model=DocumentSchema)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID"""
    
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.get("/types/", response_model=List[str])
async def get_document_types(db: AsyncSession = Depends(get_db)):
    """Get available document types"""
    
    query = select(Document.document_type).distinct()
    result = await db.execute(query)
    types = [row[0] for row in result.fetchall()]
    
    return types


@router.get("/export/csv")
async def export_documents_csv(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    customer_id: Optional[int] = Query(None, description="Filter by customer ID"),
    applicable: Optional[bool] = Query(None, description="Filter by applicable status"),
    db: AsyncSession = Depends(get_db)
):
    """Export documents to CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    # Build query
    query = select(Document)
    
    # Apply filters
    if document_type:
        query = query.where(Document.document_type == document_type)
    
    if customer_id:
        query = query.where(Document.customer_id == customer_id)
    
    if applicable is not None:
        query = query.where(Document.applicable == applicable)
    
    # Order by moment descending
    query = query.order_by(desc(Document.moment))
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "ID", "Name", "Type", "Moment", "Sum", "Currency",
        "Applicable", "State", "Organization", "Store", "Customer ID"
    ])
    
    # Write data
    for document in documents:
        writer.writerow([
            document.id,
            document.name,
            document.document_type,
            document.moment.isoformat() if document.moment else "",
            document.sum or 0,
            document.currency,
            document.applicable,
            document.state_name or "",
            document.organization_name or "",
            document.store_name or "",
            document.customer_id or ""
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=documents.csv"}
    )
