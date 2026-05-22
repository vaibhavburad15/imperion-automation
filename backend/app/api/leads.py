"""Lead capture + management endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Lead, User, Workflow, WorkflowRun
from app.schemas.schemas import LeadCreate, LeadOut
from app.services.audit import log_audit
from app.services.lead_scoring import score_lead, needs_human_handoff
from app.workers.tasks import execute_workflow_run

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=List[LeadOut])
def list_leads(limit: int = Query(100, le=500),
               user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    return db.query(Lead).filter(Lead.workspace_id == user.workspace_id).order_by(
        Lead.id.desc()).limit(limit).all()


@router.post("", response_model=LeadOut)
def create_lead(body: LeadCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    data = body.model_dump()
    score = score_lead(data)
    requires_human = needs_human_handoff(score, data)

    lead = Lead(
        workspace_id=user.workspace_id,
        name=body.name, email=body.email, phone=body.phone,
        source=body.source, data=body.data,
        score=score, requires_human=requires_human,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    log_audit(db, user.workspace_id, user.email, "lead.created", "lead", lead.id,
              {"score": score, "requires_human": requires_human})

    # Trigger all workflows with trigger_type=lead_created
    _trigger_lead_workflows(db, user.workspace_id, lead)
    return lead


@router.put("/{lead_id}/status", response_model=LeadOut)
def update_lead_status(lead_id: int, status: str,
                       user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id,
                                 Lead.workspace_id == user.workspace_id).first()
    if not lead:
        raise HTTPException(404)
    lead.status = status
    db.commit()
    db.refresh(lead)
    log_audit(db, user.workspace_id, user.email, "lead.status_updated",
              "lead", lead.id, {"status": status})
    return lead


def _trigger_lead_workflows(db: Session, workspace_id: int, lead: Lead):
    wfs = db.query(Workflow).filter(
        Workflow.workspace_id == workspace_id,
        Workflow.is_active.is_(True),
        Workflow.trigger_type == "lead_created",
    ).all()
    for wf in wfs:
        run = WorkflowRun(
            workspace_id=workspace_id, workflow_id=wf.id, status="pending",
            trigger_payload={
                "lead_id": lead.id, "name": lead.name, "email": lead.email,
                "phone": lead.phone, "source": lead.source, "score": lead.score,
                "requires_human": lead.requires_human, **(lead.data or {}),
            },
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        execute_workflow_run.delay(run.id)
