"""All SQLAlchemy ORM models for the platform.

Multi-tenant: every business object (workflow, lead, integration, audit log)
carries a workspace_id FK to enforce isolation at the row level.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text, Float, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class Workspace(Base):
    """Tenant / client workspace. Each customer gets one."""
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(60), unique=True, nullable=False, index=True)
    plan = Column(String(20), default="free")  # free / pro / enterprise
    settings = Column(JSON, default=dict)  # arbitrary per-workspace config
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="workspace", cascade="all, delete")
    workflows = relationship("Workflow", back_populates="workspace", cascade="all, delete")
    leads = relationship("Lead", back_populates="workspace", cascade="all, delete")
    integrations = relationship("Integration", back_populates="workspace", cascade="all, delete")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(120))
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="member")  # admin / member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="users")


class Integration(Base):
    """Stored credentials / config for an external service per workspace."""
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    provider = Column(String(50), nullable=False)  # gmail, sheets, calendar, slack, webhook, whatsapp, telegram
    name = Column(String(120))
    config = Column(JSON, default=dict)  # tokens, urls, channel ids, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="integrations")


class Workflow(Base):
    """A user-defined workflow: trigger -> condition -> action -> follow-up."""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text)
    # graph: {nodes: [...], edges: [...]} - each node has type/config
    graph = Column(JSON, default=dict)
    trigger_type = Column(String(50))  # webhook / schedule / manual / lead_created
    trigger_config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)
    previous_graph = Column(JSON)  # for rollback
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="workflows")
    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete")


class WorkflowRun(Base):
    """One execution of a workflow. Tracks status, retries, errors, timings."""
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"), index=True)
    status = Column(String(20), default="pending")  # pending/running/success/failed/retrying
    trigger_payload = Column(JSON)
    context = Column(JSON, default=dict)  # accumulated data through the run
    step_logs = Column(JSON, default=list)  # [{node_id, status, output, error, ts}]
    error = Column(Text)
    retry_count = Column(Integer, default=0)
    duration_ms = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)

    workflow = relationship("Workflow", back_populates="runs")

    __table_args__ = (Index("ix_runs_ws_status", "workspace_id", "status"),)


class Lead(Base):
    """A captured lead (contact). Source of conversions metric."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    name = Column(String(120))
    email = Column(String(255), index=True)
    phone = Column(String(30))
    source = Column(String(60))  # webform/api/import/etc.
    status = Column(String(30), default="new")  # new/contacted/qualified/converted/lost
    score = Column(Float, default=0.0)  # lead scoring (bonus)
    requires_human = Column(Boolean, default=False)  # handoff (bonus)
    data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="leads")


class AuditLog(Base):
    """Immutable audit trail of every important action."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    actor = Column(String(120))  # user email or 'system'
    action = Column(String(80))  # workflow.created, lead.updated, integration.deleted...
    resource_type = Column(String(40))
    resource_id = Column(String(40))
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class WebhookEvent(Base):
    """Inbound webhook events. Stored for replay & idempotency."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    source = Column(String(80))
    payload = Column(JSON)
    headers = Column(JSON)
    processed = Column(Boolean, default=False)
    received_at = Column(DateTime, default=datetime.utcnow, index=True)


class ScheduledJob(Base):
    """Schedule entries for time-based workflow triggers."""
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id", ondelete="CASCADE"))
    cron = Column(String(120))  # cron expression or "every:60" for seconds
    next_run_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
