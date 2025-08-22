from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid

class FHIRResource(Base):
    __tablename__ = "fhir_resources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_type = Column(String(50), nullable=False, index=True)
    version_id = Column(String, default="1")
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    data = Column(JSON, nullable=False)  # Will use JSONB for PostgreSQL, JSON for SQLite
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<FHIRResource(id='{self.id}', type='{self.resource_type}')>"
