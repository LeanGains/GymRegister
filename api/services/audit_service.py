from sqlalchemy.orm import Session
from ..models import AuditLog
from typing import Optional, Dict, Any
import json

class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor: str = "api_user",
        endpoint: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Log an audit event"""
        
        # Serialize payload if provided
        serialized_payload = None
        if payload:
            try:
                # Convert to dict if it's a Pydantic model
                if hasattr(payload, 'dict'):
                    payload = payload.dict()
                serialized_payload = payload
            except Exception:
                serialized_payload = {"error": "Could not serialize payload"}
        
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            endpoint=endpoint,
            payload=serialized_payload,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        resource_type: Optional[str] = None,
        action: Optional[str] = None
    ):
        """Get paginated audit logs with optional filtering"""
        query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        if action:
            query = query.filter(AuditLog.action == action)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {"items": items, "total": total}