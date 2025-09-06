from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..schemas import AnalysisJobResponse, AnalysisOut
from ..services.analysis_service import AnalysisService
from ..services.audit_service import AuditService
from ..auth import require_auth
from ..config import settings

router = APIRouter(prefix="/api", tags=["Analysis"])

# Initialize analysis service
analysis_service = AnalysisService()

@router.post("/analyze", response_model=AnalysisJobResponse, status_code=202)
async def analyze_image(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(..., description="Image file to analyze"),
    asset_tag: Optional[str] = Form(None, description="Optional asset tag to associate"),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """
    Upload an image for AI analysis.
    Returns job ID immediately and processes analysis in background.
    """
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size
    if file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size: {settings.max_file_size / 1024 / 1024:.1f}MB"
        )
    
    try:
        # Create analysis job
        analysis = analysis_service.create_analysis_job(db, file, asset_tag)
        
        # Log audit event
        AuditService.log_action(
            db=db,
            action="ANALYZE_REQUEST",
            resource_type="analysis",
            resource_id=analysis.id,
            endpoint=str(request.url),
            payload={
                "filename": file.filename,
                "asset_tag": asset_tag,
                "content_type": file.content_type
            },
            ip_address=request.client.host if request.client else None
        )
        
        # Start background processing
        background_tasks.add_task(
            process_analysis_background,
            db_session_factory=lambda: next(get_db()),
            analysis_id=analysis.id
        )
        
        return AnalysisJobResponse(
            job_id=analysis.id,
            status=analysis.status,
            message="Analysis job created successfully. Check status using the job ID."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis job: {str(e)}")

async def process_analysis_background(db_session_factory, analysis_id: str):
    """Background task to process analysis"""
    db = db_session_factory()
    try:
        analysis_service.process_analysis(db, analysis_id)
    finally:
        db.close()

@router.get("/analyze/{job_id}", response_model=AnalysisOut)
async def get_analysis_result(
    job_id: str,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get analysis result by job ID"""
    
    analysis = analysis_service.get_analysis_by_id(db, job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    return analysis

@router.get("/analysis/history", response_model=List[AnalysisOut])
async def get_analysis_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    asset_tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get paginated analysis history with optional filtering"""
    
    result = analysis_service.get_analysis_history(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        asset_tag=asset_tag
    )
    
    return result["items"]

@router.post("/analysis/reprocess/{job_id}", response_model=AnalysisJobResponse)
async def reprocess_analysis(
    job_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Reprocess a failed or completed analysis"""
    
    analysis = analysis_service.get_analysis_by_id(db, job_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    # Reset analysis status
    analysis.status = "pending"
    analysis.error_message = None
    analysis.result = None
    analysis.completed_at = None
    analysis.processing_time = None
    db.commit()
    
    # Log audit event
    AuditService.log_action(
        db=db,
        action="ANALYZE_REPROCESS",
        resource_type="analysis",
        resource_id=analysis.id,
        endpoint=str(request.url),
        ip_address=request.client.host if request.client else None
    )
    
    # Start background processing
    background_tasks.add_task(
        process_analysis_background,
        db_session_factory=lambda: next(get_db()),
        analysis_id=analysis.id
    )
    
    return AnalysisJobResponse(
        job_id=analysis.id,
        status=analysis.status,
        message="Analysis reprocessing started"
    )