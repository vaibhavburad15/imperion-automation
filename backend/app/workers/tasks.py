"""Celery tasks — async workflow execution with retry/backoff."""
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.logger import logger
from app.models import Workflow, WorkflowRun
from app.workflows.engine import WorkflowEngine


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def execute_workflow_run(self, run_id: int):
    """Pick up a WorkflowRun row and execute it through the engine."""
    db = SessionLocal()
    try:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            logger.warning(f"WorkflowRun {run_id} not found")
            return
        workflow = db.query(Workflow).filter(Workflow.id == run.workflow_id).first()
        if not workflow:
            run.status = "failed"
            run.error = "Workflow deleted"
            db.commit()
            return
        engine = WorkflowEngine(workflow, run, db)
        result = engine.execute()
        logger.info(f"Run {run_id} finished: {result['status']}")
        return result
    except Exception as exc:
        logger.exception(f"Task execute_workflow_run failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task
def replay_webhook(event_id: int):
    """Replay a stored webhook event (bonus feature)."""
    from app.models import WebhookEvent
    db = SessionLocal()
    try:
        ev = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
        if not ev:
            return
        workflow = db.query(Workflow).filter(Workflow.id == ev.workflow_id).first()
        if not workflow:
            return
        run = WorkflowRun(
            workspace_id=ev.workspace_id,
            workflow_id=workflow.id,
            status="pending",
            trigger_payload=ev.payload or {},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        execute_workflow_run.delay(run.id)
        ev.processed = True
        db.commit()
    finally:
        db.close()
