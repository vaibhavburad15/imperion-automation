"""Workspace endpoints (current workspace info + settings update)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Workspace, User
from app.schemas.schemas import WorkspaceOut
from app.services.audit import log_audit

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/me", response_model=WorkspaceOut)
def get_my_workspace(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    return ws


@router.put("/settings", response_model=WorkspaceOut)
def update_settings(settings: dict, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    ws = db.query(Workspace).filter(Workspace.id == user.workspace_id).first()
    ws.settings = {**(ws.settings or {}), **settings}
    db.commit()
    db.refresh(ws)
    log_audit(db, ws.id, user.email, "workspace.settings_updated", "workspace", ws.id, settings)
    return ws
