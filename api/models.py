from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.sql import func
from .database import Base
import uuid
from datetime import datetime

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_tag = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    item_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=False)
    status = Column(String, default="Active")  # Active, Missing, Out of Service
    condition = Column(String, default="Good")  # Excellent, Good, Fair, Poor, Needs Repair
    weight = Column(String, nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    asset_tag = Column(String, nullable=True)  # Can be null if no asset found
    image_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE, ANALYZE, etc.
    resource_type = Column(String, nullable=False)  # asset, analysis, etc.
    resource_id = Column(String, nullable=True)
    actor = Column(String, default="api_user")  # Could be user ID in future
    endpoint = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)