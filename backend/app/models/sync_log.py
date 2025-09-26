"""
Sync log model for tracking synchronization operations
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, Boolean
from sqlalchemy.sql import func

from app.models.base import Base, TimestampMixin


class SyncLog(Base, TimestampMixin):
    """Sync log model"""
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String(50), nullable=False, comment="Type of sync operation")
    entity_type = Column(String(50), nullable=True, comment="Entity type being synced")
    
    # Status
    status = Column(String(20), nullable=False, comment="Sync status: success, error, in_progress")
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Sync start time")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="Sync completion time")
    
    # Results
    records_processed = Column(Integer, default=0, comment="Number of records processed")
    records_created = Column(Integer, default=0, comment="Number of records created")
    records_updated = Column(Integer, default=0, comment="Number of records updated")
    records_errors = Column(Integer, default=0, comment="Number of records with errors")
    
    # Error information
    error_message = Column(Text, nullable=True, comment="Error message if sync failed")
    error_details = Column(Text, nullable=True, comment="Detailed error information")
    
    # Request/Response data
    request_payload = Column(Text, nullable=True, comment="Request payload")
    response_payload = Column(Text, nullable=True, comment="Response payload")
    
    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, type='{self.sync_type}', status='{self.status}')>"
