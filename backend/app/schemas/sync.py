"""
Sync schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    """Sync request schema"""
    sync_type: str = Field(..., description="Type of sync: full, incremental, products, customers, documents")
    force: bool = Field(False, description="Force sync even if recently synced")


class SyncResponse(BaseModel):
    """Sync response schema"""
    message: str = Field(..., description="Response message")
    sync_id: Optional[int] = Field(None, description="Sync log ID")
    status: str = Field(..., description="Sync status")


class SyncLogBase(BaseModel):
    """Base sync log schema"""
    sync_type: str = Field(..., description="Type of sync operation")
    entity_type: Optional[str] = Field(None, description="Entity type being synced")
    status: str = Field(..., description="Sync status")
    records_processed: int = Field(0, description="Number of records processed")
    records_created: int = Field(0, description="Number of records created")
    records_updated: int = Field(0, description="Number of records updated")
    records_errors: int = Field(0, description="Number of records with errors")
    error_message: Optional[str] = Field(None, description="Error message")
    started_at: datetime = Field(..., description="Sync start time")
    completed_at: Optional[datetime] = Field(None, description="Sync completion time")


class SyncLog(SyncLogBase):
    """Sync log response schema"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
