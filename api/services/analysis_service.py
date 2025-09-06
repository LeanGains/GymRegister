import os
import uuid
import shutil
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from ..models import AnalysisHistory, Asset
from ..config import settings
from .ai_service import AIService
from .asset_service import AssetService

class AnalysisService:
    def __init__(self):
        self.ai_service = AIService()
        
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)
    
    def create_analysis_job(
        self,
        db: Session,
        file: UploadFile,
        asset_tag: Optional[str] = None
    ) -> AnalysisHistory:
        """Create a new analysis job and save the uploaded file"""
        
        # Generate unique filename
        job_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename or "image.jpg")[1]
        filename = f"{job_id}{file_extension}"
        file_path = os.path.join(settings.upload_dir, filename)
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create analysis record
        analysis = AnalysisHistory(
            id=job_id,
            asset_tag=asset_tag.upper() if asset_tag else None,
            image_path=file_path,
            original_filename=file.filename,
            status="pending"
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        return analysis
    
    def process_analysis(self, db: Session, analysis_id: str) -> Optional[AnalysisHistory]:
        """Process the analysis using AI service"""
        
        # Get analysis record
        analysis = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
        if not analysis:
            return None
        
        start_time = datetime.utcnow()
        
        try:
            # Update status to processing
            analysis.status = "processing"
            db.commit()
            
            # Perform AI analysis
            result = self.ai_service.analyze_gym_equipment(
                analysis.image_path, 
                analysis.asset_tag
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update analysis record
            if result.get("error"):
                analysis.status = "failed"
                analysis.error_message = result["error"]
            else:
                analysis.status = "completed"
                analysis.result = result
                analysis.confidence_score = result.get("confidence_score", 0.5)
            
            analysis.completed_at = datetime.utcnow()
            analysis.processing_time = processing_time
            
            db.commit()
            db.refresh(analysis)
            
            # Try to auto-update asset if asset_tag provided and found
            if analysis.asset_tag and analysis.status == "completed":
                self._try_auto_update_asset(db, analysis)
            
            return analysis
            
        except Exception as e:
            # Update analysis record with error
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            analysis.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            db.commit()
            db.refresh(analysis)
            
            return analysis
    
    def _try_auto_update_asset(self, db: Session, analysis: AnalysisHistory):
        """Try to automatically update asset based on analysis results"""
        try:
            if not analysis.asset_tag or not analysis.result:
                return
            
            # Check if asset exists
            asset = AssetService.get_asset_by_tag(db, analysis.asset_tag)
            if not asset:
                return
            
            # Update last_seen timestamp
            asset.last_seen = datetime.utcnow()
            
            # If equipment was detected, update asset information
            equipment_list = analysis.result.get("equipment", [])
            if equipment_list:
                # Use first detected equipment for updates
                equipment = equipment_list[0]
                
                # Update condition if detected and different
                detected_condition = equipment.get("condition", "").lower()
                condition_mapping = {
                    "excellent": "Excellent",
                    "good": "Good", 
                    "fair": "Fair",
                    "poor": "Poor"
                }
                
                if detected_condition in condition_mapping:
                    new_condition = condition_mapping[detected_condition]
                    if asset.condition != new_condition:
                        asset.condition = new_condition
                
                # Update weight if not set and detected
                if not asset.weight and equipment.get("weight", "unknown") != "unknown":
                    asset.weight = equipment.get("weight")
                
                # Update description if empty and detected
                if not asset.description and equipment.get("description"):
                    asset.description = equipment.get("description")
            
            asset.updated_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            # Don't fail the analysis if auto-update fails
            print(f"Auto-update failed for asset {analysis.asset_tag}: {e}")
    
    def get_analysis_by_id(self, db: Session, analysis_id: str) -> Optional[AnalysisHistory]:
        """Get analysis by ID"""
        return db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
    
    def get_analysis_history(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        asset_tag: Optional[str] = None
    ):
        """Get paginated analysis history"""
        query = db.query(AnalysisHistory).order_by(AnalysisHistory.created_at.desc())
        
        if status:
            query = query.filter(AnalysisHistory.status == status)
        
        if asset_tag:
            query = query.filter(AnalysisHistory.asset_tag == asset_tag.upper())
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}
    
    def cleanup_old_files(self, db: Session, days: int = 30):
        """Clean up old analysis files (optional maintenance task)"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_analyses = db.query(AnalysisHistory).filter(
            AnalysisHistory.created_at < cutoff_date,
            AnalysisHistory.status.in_(["completed", "failed"])
        ).all()
        
        deleted_count = 0
        for analysis in old_analyses:
            try:
                if os.path.exists(analysis.image_path):
                    os.remove(analysis.image_path)
                db.delete(analysis)
                deleted_count += 1
            except Exception as e:
                print(f"Failed to cleanup analysis {analysis.id}: {e}")
        
        if deleted_count > 0:
            db.commit()
        
        return deleted_count