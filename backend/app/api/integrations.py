"""Integration CRUD per workspace."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Integration, User
from app.schemas.schemas import IntegrationCreate, IntegrationOut
from app.integrations import REGISTRY
from app.services.audit import log_audit

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers")
def list_providers():
    return {"providers": list(REGISTRY.keys())}


@router.get("", response_model=List[IntegrationOut])
def list_integrations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Integration).filter(Integration.workspace_id == user.workspace_id).all()


@router.post("", response_model=IntegrationOut)
def create_integration(body: IntegrationCreate, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    if body.provider.lower() not in REGISTRY:
        raise HTTPException(400, f"Unknown provider: {body.provider}")
    integ = Integration(
        workspace_id=user.workspace_id,
        provider=body.provider.lower(),
        name=body.name or body.provider,
        config=body.config,
    )
    db.add(integ)
    db.commit()
    db.refresh(integ)
    log_audit(db, user.workspace_id, user.email, "integration.created",
              "integration", integ.id, {"provider": integ.provider})
    return integ


@router.delete("/{integration_id}")
def delete_integration(integration_id: int, user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    integ = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.workspace_id == user.workspace_id,
    ).first()
    if not integ:
        raise HTTPException(404, "Integration not found")
    db.delete(integ)
    db.commit()
    log_audit(db, user.workspace_id, user.email, "integration.deleted",
              "integration", integration_id)
    return {"deleted": True}


@router.post("/{integration_id}/test")
def test_integration(integration_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    integ = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.workspace_id == user.workspace_id,
    ).first()
    if not integ:
        raise HTTPException(404, "Integration not found")
    handler = REGISTRY[integ.provider]()
    try:
        result = handler.execute(
            "send",
            {**(integ.config or {}), "to": integ.config.get("to", "test@example.com"),
             "subject": "Test", "body": "Test message", "text": "Test message"},
            {"name": "Test User", "email": "test@example.com"},
        )
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
