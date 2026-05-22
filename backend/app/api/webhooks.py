"""Inbound webhook receiver + replay endpoint."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Workflow, WorkflowRun, WebhookEvent, User
from app.api.deps import get_current_user
from app.workers.tasks import execute_workflow_run, replay_webhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/{workspace_slug}/{workflow_id}")
async def receive_webhook(workspace_slug: str, workflow_id: int,
                          request: Request, db: Session = Depends(get_db)):
    """Public endpoint — no auth (signature could be added in production)."""
    from app.models import Workspace
    ws = db.query(Workspace).filter(Workspace.slug == workspace_slug,
                                    Workspace.is_active.is_(True)).first()
    if not ws:
        raise HTTPException(404, "Workspace not found")
    wf = db.query(Workflow).filter(
        Workflow.id == workflow_id, Workflow.workspace_id == ws.id,
        Workflow.is_active.is_(True),
    ).first()
    if not wf:
        raise HTTPException(404, "Workflow not found")

    try:
        payload = await request.json()
    except Exception:
        payload = dict(await request.form())

    headers = dict(request.headers)
    ev = WebhookEvent(workspace_id=ws.id, workflow_id=wf.id,
                      source="http", payload=payload, headers=headers)
    db.add(ev)
    db.commit()
    db.refresh(ev)

    run = WorkflowRun(workspace_id=ws.id, workflow_id=wf.id,
                      status="pending", trigger_payload=payload)
    db.add(run)
    db.commit()
    db.refresh(run)
    execute_workflow_run.delay(run.id)

    ev.processed = True
    db.commit()
    return {"received": True, "event_id": ev.id, "run_id": run.id}


@router.get("/events")
def list_webhook_events(limit: int = 100,
                        user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    return db.query(WebhookEvent).filter(
        WebhookEvent.workspace_id == user.workspace_id
    ).order_by(WebhookEvent.id.desc()).limit(limit).all()


@router.post("/events/{event_id}/replay")
def replay_event(event_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    ev = db.query(WebhookEvent).filter(
        WebhookEvent.id == event_id,
        WebhookEvent.workspace_id == user.workspace_id,
    ).first()
    if not ev:
        raise HTTPException(404)
    replay_webhook.delay(ev.id)
    return {"queued": True}
