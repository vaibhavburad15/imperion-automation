"""Workflow CRUD + run management."""
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Workflow, WorkflowRun, User, ScheduledJob
from app.schemas.schemas import (
    WorkflowCreate, WorkflowOut, WorkflowRunOut, RunTriggerRequest,
)
from app.services.audit import log_audit
from app.workers.tasks import execute_workflow_run

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=List[WorkflowOut])
def list_workflows(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Workflow).filter(
        Workflow.workspace_id == user.workspace_id
    ).order_by(Workflow.id.desc()).all()


@router.post("", response_model=WorkflowOut)
def create_workflow(body: WorkflowCreate, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    wf = Workflow(
        workspace_id=user.workspace_id,
        name=body.name,
        description=body.description,
        graph=body.graph,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config,
        is_active=body.is_active,
    )
    db.add(wf)
    db.commit()
    db.refresh(wf)

    # If scheduled trigger, create ScheduledJob
    if body.trigger_type == "schedule":
        interval = body.trigger_config.get("interval", "every:3600")
        job = ScheduledJob(
            workspace_id=user.workspace_id, workflow_id=wf.id,
            cron=interval, next_run_at=datetime.utcnow() + timedelta(seconds=30),
        )
        db.add(job)
        db.commit()

    log_audit(db, user.workspace_id, user.email, "workflow.created", "workflow", wf.id)
    return wf


@router.get("/{wf_id}", response_model=WorkflowOut)
def get_workflow(wf_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(
        Workflow.id == wf_id, Workflow.workspace_id == user.workspace_id
    ).first()
    if not wf:
        raise HTTPException(404)
    return wf


@router.put("/{wf_id}", response_model=WorkflowOut)
def update_workflow(wf_id: int, body: WorkflowCreate,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(
        Workflow.id == wf_id, Workflow.workspace_id == user.workspace_id
    ).first()
    if not wf:
        raise HTTPException(404)
    # Save previous graph for rollback (reliability layer)
    wf.previous_graph = wf.graph
    wf.name = body.name
    wf.description = body.description
    wf.graph = body.graph
    wf.trigger_type = body.trigger_type
    wf.trigger_config = body.trigger_config
    wf.is_active = body.is_active
    wf.version += 1
    db.commit()
    db.refresh(wf)
    log_audit(db, user.workspace_id, user.email, "workflow.updated", "workflow", wf.id,
              {"version": wf.version})
    return wf


@router.post("/{wf_id}/rollback", response_model=WorkflowOut)
def rollback_workflow(wf_id: int, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """Safe rollback to previous graph version."""
    wf = db.query(Workflow).filter(
        Workflow.id == wf_id, Workflow.workspace_id == user.workspace_id
    ).first()
    if not wf or not wf.previous_graph:
        raise HTTPException(400, "No previous version to roll back to")
    current = wf.graph
    wf.graph = wf.previous_graph
    wf.previous_graph = current
    wf.version += 1
    db.commit()
    db.refresh(wf)
    log_audit(db, user.workspace_id, user.email, "workflow.rolled_back",
              "workflow", wf.id, {"version": wf.version})
    return wf


@router.delete("/{wf_id}")
def delete_workflow(wf_id: int, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(
        Workflow.id == wf_id, Workflow.workspace_id == user.workspace_id
    ).first()
    if not wf:
        raise HTTPException(404)
    db.delete(wf)
    db.commit()
    log_audit(db, user.workspace_id, user.email, "workflow.deleted", "workflow", wf_id)
    return {"deleted": True}


@router.post("/{wf_id}/run", response_model=WorkflowRunOut)
def trigger_run(wf_id: int, body: RunTriggerRequest,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    wf = db.query(Workflow).filter(
        Workflow.id == wf_id, Workflow.workspace_id == user.workspace_id
    ).first()
    if not wf:
        raise HTTPException(404)
    if not wf.is_active:
        raise HTTPException(400, "Workflow is inactive")
    run = WorkflowRun(
        workspace_id=user.workspace_id, workflow_id=wf.id,
        status="pending", trigger_payload=body.payload,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    execute_workflow_run.delay(run.id)
    log_audit(db, user.workspace_id, user.email, "workflow.run_triggered",
              "workflow_run", run.id)
    return run


@router.get("/{wf_id}/runs", response_model=List[WorkflowRunOut])
def list_runs(wf_id: int, limit: int = Query(50, le=200),
              user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    return db.query(WorkflowRun).filter(
        WorkflowRun.workflow_id == wf_id,
        WorkflowRun.workspace_id == user.workspace_id,
    ).order_by(WorkflowRun.id.desc()).limit(limit).all()


@router.get("/runs/all", response_model=List[WorkflowRunOut])
def list_all_runs(limit: int = Query(100, le=500),
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    return db.query(WorkflowRun).filter(
        WorkflowRun.workspace_id == user.workspace_id,
    ).order_by(WorkflowRun.id.desc()).limit(limit).all()
