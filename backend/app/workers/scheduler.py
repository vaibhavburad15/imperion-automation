"""APScheduler-based job runner for scheduled workflow triggers."""
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.database import SessionLocal
from app.core.logger import logger
from app.models import ScheduledJob, Workflow, WorkflowRun
from app.workers.tasks import execute_workflow_run

_scheduler: BackgroundScheduler = None


def _tick():
    """Every 30s, scan for due scheduled jobs and enqueue runs."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        due = db.query(ScheduledJob).filter(
            ScheduledJob.is_active.is_(True),
            ScheduledJob.next_run_at <= now,
        ).all()
        for job in due:
            wf = db.query(Workflow).filter(Workflow.id == job.workflow_id,
                                           Workflow.is_active.is_(True)).first()
            if not wf:
                continue
            run = WorkflowRun(
                workspace_id=job.workspace_id,
                workflow_id=wf.id,
                status="pending",
                trigger_payload={"_scheduled": True, "_job_id": job.id},
            )
            db.add(run)
            db.commit()
            db.refresh(run)
            execute_workflow_run.delay(run.id)

            # Compute next run
            interval = _parse_interval(job.cron)
            job.next_run_at = now + timedelta(seconds=interval)
            db.commit()
            logger.info(f"Scheduled job {job.id} fired, next at {job.next_run_at}")
    except Exception:
        logger.exception("Scheduler tick failed")
    finally:
        db.close()


def _parse_interval(cron_or_interval: str) -> int:
    """Supports 'every:60' (seconds) or default 3600s."""
    if cron_or_interval and cron_or_interval.startswith("every:"):
        try:
            return int(cron_or_interval.split(":", 1)[1])
        except ValueError:
            return 3600
    return 3600


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_tick, "interval", seconds=30, id="tick", replace_existing=True)
    _scheduler.start()
    logger.info("APScheduler started")
    return _scheduler
