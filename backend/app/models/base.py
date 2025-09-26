"""
Base model class with common fields
"""
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at fields"""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class ExternalDataMixin:
    """Mixin for external system data"""
    external_id = Column(String(255), nullable=False, index=True, comment="External system ID")
    external_raw = Column(Text, nullable=True, comment="Raw JSON data from external system")
    external_updated = Column(DateTime(timezone=True), nullable=True, comment="Last update from external system")
