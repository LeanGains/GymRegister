from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from ..schemas import AssetCreate, AssetUpdate, AssetOut, APIResponse
from ..services.asset_service import AssetService
from ..services.audit_service import AuditService
from ..auth import require_auth

router = APIRouter(prefix="/api/assets", tags=["Assets"])

@router.post("/", response_model=AssetOut, status_code=201)
async def create_asset(
    asset_data: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Create a new asset"""
    
    # Check if asset tag already exists
    existing = AssetService.get_asset_by_tag(db, asset_data.asset_tag)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Asset with tag '{asset_data.asset_tag}' already exists"
        )
    
    try:
        # Create asset
        asset = AssetService.create_asset(db, asset_data)
        
        # Log audit event
        AuditService.log_action(
            db=db,
            action="CREATE",
            resource_type="asset",
            resource_id=asset.id,
            endpoint=str(request.url),
            payload=asset_data.dict(),
            ip_address=request.client.host if request.client else None
        )
        
        return asset
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create asset: {str(e)}")

@router.get("/", response_model=List[AssetOut])
async def get_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    condition: Optional[str] = Query(None),
    item_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get paginated list of assets with optional filtering"""
    
    result = AssetService.get_assets(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        condition=condition,
        item_type=item_type,
        location=location,
        search=search
    )
    
    return result["items"]

@router.get("/{asset_tag}", response_model=AssetOut)
async def get_asset(
    asset_tag: str,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Get asset by tag"""
    
    asset = AssetService.get_asset_by_tag(db, asset_tag)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    return asset

@router.put("/{asset_tag}", response_model=AssetOut)
async def update_asset(
    asset_tag: str,
    asset_update: AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Update an existing asset"""
    
    # Check if asset exists
    existing = AssetService.get_asset_by_tag(db, asset_tag)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        # Update asset
        updated_asset = AssetService.update_asset(db, asset_tag, asset_update)
        
        # Log audit event
        AuditService.log_action(
            db=db,
            action="UPDATE",
            resource_type="asset",
            resource_id=updated_asset.id,
            endpoint=str(request.url),
            payload=asset_update.dict(exclude_unset=True),
            ip_address=request.client.host if request.client else None
        )
        
        return updated_asset
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update asset: {str(e)}")

@router.delete("/{asset_tag}", status_code=204)
async def delete_asset(
    asset_tag: str,
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Delete an asset"""
    
    # Check if asset exists
    existing = AssetService.get_asset_by_tag(db, asset_tag)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    try:
        # Delete asset
        success = AssetService.delete_asset(db, asset_tag)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete asset")
        
        # Log audit event
        AuditService.log_action(
            db=db,
            action="DELETE",
            resource_type="asset",
            resource_id=existing.id,
            endpoint=str(request.url),
            payload={"asset_tag": asset_tag},
            ip_address=request.client.host if request.client else None
        )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete asset: {str(e)}")

@router.patch("/{asset_tag}/location")
async def update_asset_location(
    asset_tag: str,
    location: str = Query(..., description="New location"),
    request: Request,
    db: Session = Depends(get_db),
    auth: dict = Depends(require_auth)
):
    """Update asset location (convenience endpoint)"""
    
    asset = AssetService.update_asset_location(db, asset_tag, location)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Log audit event
    AuditService.log_action(
        db=db,
        action="LOCATION_UPDATE",
        resource_type="asset",
        resource_id=asset.id,
        endpoint=str(request.url),
        payload={"asset_tag": asset_tag, "new_location": location},
        ip_address=request.client.host if request.client else None
    )
    
    return {"message": "Location updated successfully", "asset": asset}