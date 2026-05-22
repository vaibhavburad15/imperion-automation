"""Audit logging helper."""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import AuditLog


def log_audit(db: Session, workspace_id: int, actor: str, action: str,
              resource_type: str, resource_id: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None):
    entry = AuditLog(
        workspace_id=workspace_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details or {},
    )
    db.add(entry)
    db.commit()
    return entry
