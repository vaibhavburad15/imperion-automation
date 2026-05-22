"""Analytics + audit log + admin endpoints."""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import Lead, WorkflowRun, Workflow, AuditLog, User
from app.schemas.schemas import AnalyticsResponse

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws_id = user.workspace_id
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)

    total_leads = db.query(func.count(Lead.id)).filter(Lead.workspace_id == ws_id).scalar() or 0
    leads_today = db.query(func.count(Lead.id)).filter(
        Lead.workspace_id == ws_id, Lead.created_at >= today_start
    ).scalar() or 0
    converted = db.query(func.count(Lead.id)).filter(
        Lead.workspace_id == ws_id, Lead.status == "converted"
    ).scalar() or 0

    total_runs = db.query(func.count(WorkflowRun.id)).filter(
        WorkflowRun.workspace_id == ws_id).scalar() or 0
    success_runs = db.query(func.count(WorkflowRun.id)).filter(
        WorkflowRun.workspace_id == ws_id, WorkflowRun.status == "success").scalar() or 0
    failed_runs = db.query(func.count(WorkflowRun.id)).filter(
        WorkflowRun.workspace_id == ws_id, WorkflowRun.status == "failed").scalar() or 0
    avg_ms = db.query(func.avg(WorkflowRun.duration_ms)).filter(
        WorkflowRun.workspace_id == ws_id, WorkflowRun.duration_ms.isnot(None)
    ).scalar() or 0.0
    active_wfs = db.query(func.count(Workflow.id)).filter(
        Workflow.workspace_id == ws_id, Workflow.is_active.is_(True)
    ).scalar() or 0

    runs_by_status_rows = db.query(WorkflowRun.status, func.count(WorkflowRun.id)).filter(
        WorkflowRun.workspace_id == ws_id
    ).group_by(WorkflowRun.status).all()
    runs_by_status = {s: c for s, c in runs_by_status_rows}

    # last 7 days runs
    runs_7d = []
    for i in range(6, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        c = db.query(func.count(WorkflowRun.id)).filter(
            WorkflowRun.workspace_id == ws_id,
            WorkflowRun.started_at >= day_start,
            WorkflowRun.started_at < day_end,
        ).scalar() or 0
        runs_7d.append({"date": day_start.strftime("%Y-%m-%d"), "count": c})

    conv_rate = (converted / total_leads * 100) if total_leads else 0.0

    return AnalyticsResponse(
        total_leads=total_leads, leads_today=leads_today,
        total_runs=total_runs, success_runs=success_runs, failed_runs=failed_runs,
        avg_response_ms=float(avg_ms), conversion_rate=round(conv_rate, 2),
        active_workflows=active_wfs, runs_by_status=runs_by_status,
        runs_last_7_days=runs_7d,
    )


@router.get("/audit-logs")
def get_audit_logs(limit: int = 200,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    rows = db.query(AuditLog).filter(
        AuditLog.workspace_id == user.workspace_id
    ).order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "actor": r.actor, "action": r.action,
            "resource_type": r.resource_type, "resource_id": r.resource_id,
            "details": r.details, "created_at": r.created_at,
        } for r in rows
    ]
