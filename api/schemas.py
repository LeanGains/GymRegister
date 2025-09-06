from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for validation
class AssetStatus(str, Enum):
    ACTIVE = "Active"
    MISSING = "Missing"
    OUT_OF_SERVICE = "Out of Service"

class AssetCondition(str, Enum):
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    NEEDS_REPAIR = "Needs Repair"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Asset Schemas
class AssetBase(BaseModel):
    asset_tag: str = Field(..., description="Unique asset tag")
    name: Optional[str] = Field(None, description="Asset name")
    item_type: str = Field(..., description="Type of equipment")
    description: Optional[str] = Field(None, description="Asset description")
    location: str = Field(..., description="Current location")
    status: AssetStatus = Field(AssetStatus.ACTIVE, description="Asset status")
    condition: AssetCondition = Field(AssetCondition.GOOD, description="Asset condition")
    weight: Optional[str] = Field(None, description="Weight specification")
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    item_type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    status: Optional[AssetStatus] = None
    condition: Optional[AssetCondition] = None
    weight: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AssetOut(AssetBase):
    id: str
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Analysis Schemas
class AnalysisRequest(BaseModel):
    asset_tag: Optional[str] = Field(None, description="Optional asset tag to associate")
    description: Optional[str] = Field(None, description="Optional description")

class AnalysisOut(BaseModel):
    id: str
    asset_tag: Optional[str]
    original_filename: Optional[str]
    status: AnalysisStatus
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    confidence_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    processing_time: Optional[float]

    class Config:
        from_attributes = True

class AnalysisJobResponse(BaseModel):
    job_id: str
    status: AnalysisStatus
    message: str

# Report Schemas
class AssetStatistics(BaseModel):
    total_assets: int
    by_status: Dict[str, int]
    by_condition: Dict[str, int]
    by_type: Dict[str, int]
    by_location: Dict[str, int]
    last_updated: datetime

class AuditLogOut(BaseModel):
    id: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    actor: str
    endpoint: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True

# Pagination
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# API Response wrappers
class APIResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None