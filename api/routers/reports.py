from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io
from datetime import datetime
from ..database import get_db
from ..schemas import AssetStatistics, AuditLogOut, AssetOut
from ..services.asset_service import AssetService
from ..services.audit_service import AuditService
from ..auth import require_auth

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/statistics", response_model=AssetStatistics)
async def get_asset_statistics(
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get comprehensive asset statistics"""
    
    try:
        stats = AssetService.get_statistics(db)
        return AssetStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.get("/audit-logs", response_model=List[AuditLogOut])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    resource_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get paginated audit logs with optional filtering"""
    
    try:
        result = AuditService.get_audit_logs(
            db=db,
            skip=skip,
            limit=limit,
            resource_type=resource_type,
            action=action
        )
        
        return result["items"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}")

@router.get("/export")
async def export_assets_csv(
    status: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Export assets to CSV file"""
    
    try:
        # Get filtered assets
        result = AssetService.get_assets(
            db=db,
            skip=0,
            limit=10000,  # Large limit for export
            status=status,
            condition=condition,
            item_type=item_type,
            location=location
        )
        
        assets = result["items"]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            "Asset Tag", "Name", "Type", "Description", "Location", 
            "Status", "Condition", "Weight", "Last Seen", 
            "Created At", "Updated At", "Notes"
        ]
        writer.writerow(headers)
        
        # Write data rows
        for asset in assets:
            writer.writerow([
                asset.asset_tag,
                asset.name or "",
                asset.item_type,
                asset.description or "",
                asset.location,
                asset.status,
                asset.condition,
                asset.weight or "",
                asset.last_seen.isoformat() if asset.last_seen else "",
                asset.created_at.isoformat() if asset.created_at else "",
                asset.updated_at.isoformat() if asset.updated_at else "",
                asset.notes or ""
            ])
        
        # Prepare response
        csv_content = output.getvalue()
        output.close()
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gym_assets_{timestamp}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export assets: {str(e)}")

@router.get("/missing", response_model=List[AssetOut])
async def get_missing_assets(
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get assets flagged as missing"""
    
    try:
        attention_assets = AssetService.get_assets_needing_attention(db)
        return attention_assets["missing"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get missing assets: {str(e)}")

@router.get("/repair", response_model=List[AssetOut])
async def get_assets_needing_repair(
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get assets needing repair"""
    
    try:
        attention_assets = AssetService.get_assets_needing_attention(db)
        return attention_assets["needs_repair"]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get repair assets: {str(e)}")

@router.get("/dashboard")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get comprehensive dashboard data"""
    
    try:
        # Get statistics
        stats = AssetService.get_statistics(db)
        
        # Get assets needing attention
        attention = AssetService.get_assets_needing_attention(db)
        
        # Get recent assets (last 10)
        recent_assets = AssetService.get_assets(db, skip=0, limit=10)
        
        return {
            "statistics": stats,
            "missing_assets": len(attention["missing"]),
            "repair_assets": len(attention["needs_repair"]),
            "recent_assets": recent_assets["items"],
            "alerts": {
                "missing_count": len(attention["missing"]),
                "repair_count": len(attention["needs_repair"]),
                "has_alerts": len(attention["missing"]) > 0 or len(attention["needs_repair"]) > 0
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")