from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from ..models import Asset
from ..schemas import AssetCreate, AssetUpdate
from typing import Optional, List, Dict, Any
from datetime import datetime

class AssetService:
    @staticmethod
    def create_asset(db: Session, asset_data: AssetCreate) -> Asset:
        """Create a new asset"""
        # Convert Pydantic model to dict
        asset_dict = asset_data.dict()
        asset_dict['asset_tag'] = asset_dict['asset_tag'].upper()
        asset_dict['last_seen'] = datetime.utcnow()
        
        db_asset = Asset(**asset_dict)
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        return db_asset
    
    @staticmethod
    def get_asset_by_tag(db: Session, asset_tag: str) -> Optional[Asset]:
        """Get asset by tag"""
        return db.query(Asset).filter(Asset.asset_tag == asset_tag.upper()).first()
    
    @staticmethod
    def get_asset_by_id(db: Session, asset_id: str) -> Optional[Asset]:
        """Get asset by ID"""
        return db.query(Asset).filter(Asset.id == asset_id).first()
    
    @staticmethod
    def get_assets(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        condition: Optional[str] = None,
        item_type: Optional[str] = None,
        location: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of assets with optional filtering"""
        query = db.query(Asset)
        
        # Apply filters
        if status:
            query = query.filter(Asset.status == status)
        
        if condition:
            query = query.filter(Asset.condition == condition)
        
        if item_type:
            query = query.filter(Asset.item_type == item_type)
        
        if location:
            query = query.filter(Asset.location.ilike(f"%{location}%"))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Asset.asset_tag.ilike(search_term),
                    Asset.name.ilike(search_term),
                    Asset.description.ilike(search_term),
                    Asset.location.ilike(search_term)
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        items = query.order_by(Asset.updated_at.desc()).offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}
    
    @staticmethod
    def update_asset(db: Session, asset_tag: str, asset_update: AssetUpdate) -> Optional[Asset]:
        """Update an existing asset"""
        db_asset = AssetService.get_asset_by_tag(db, asset_tag)
        if not db_asset:
            return None
        
        # Update only provided fields
        update_data = asset_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_asset, field, value)
        
        db_asset.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_asset)
        return db_asset
    
    @staticmethod
    def update_asset_location(db: Session, asset_tag: str, location: str) -> Optional[Asset]:
        """Update asset location and last_seen timestamp"""
        db_asset = AssetService.get_asset_by_tag(db, asset_tag)
        if not db_asset:
            return None
        
        db_asset.location = location
        db_asset.last_seen = datetime.utcnow()
        db_asset.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_asset)
        return db_asset
    
    @staticmethod
    def delete_asset(db: Session, asset_tag: str) -> bool:
        """Delete an asset"""
        db_asset = AssetService.get_asset_by_tag(db, asset_tag)
        if not db_asset:
            return False
        
        db.delete(db_asset)
        db.commit()
        return True
    
    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
        """Get asset statistics"""
        total_assets = db.query(Asset).count()
        
        # Status breakdown
        status_stats = db.query(Asset.status, func.count(Asset.id)).group_by(Asset.status).all()
        status_dict = {status: count for status, count in status_stats}
        
        # Condition breakdown
        condition_stats = db.query(Asset.condition, func.count(Asset.id)).group_by(Asset.condition).all()
        condition_dict = {condition: count for condition, count in condition_stats}
        
        # Type breakdown
        type_stats = db.query(Asset.item_type, func.count(Asset.id)).group_by(Asset.item_type).all()
        type_dict = {item_type: count for item_type, count in type_stats}
        
        # Location breakdown
        location_stats = db.query(Asset.location, func.count(Asset.id)).group_by(Asset.location).all()
        location_dict = {location: count for location, count in location_stats}
        
        return {
            "total_assets": total_assets,
            "by_status": status_dict,
            "by_condition": condition_dict,
            "by_type": type_dict,
            "by_location": location_dict,
            "last_updated": datetime.utcnow()
        }
    
    @staticmethod
    def get_assets_needing_attention(db: Session) -> Dict[str, List[Asset]]:
        """Get assets that need attention (missing or need repair)"""
        missing_assets = db.query(Asset).filter(Asset.status == "Missing").all()
        repair_assets = db.query(Asset).filter(Asset.condition == "Needs Repair").all()
        
        return {
            "missing": missing_assets,
            "needs_repair": repair_assets
        }