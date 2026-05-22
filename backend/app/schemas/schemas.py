"""Pydantic request/response schemas."""
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    workspace_id: int
    user_id: int
    email: str


# ---------- Workspace ----------
class WorkspaceOut(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    settings: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Integration ----------
class IntegrationCreate(BaseModel):
    provider: str
    name: Optional[str] = None
    config: Dict[str, Any] = {}


class IntegrationOut(IntegrationCreate):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Workflow ----------
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    graph: Dict[str, Any]  # {nodes: [...], edges: [...]}
    trigger_type: str = "manual"
    trigger_config: Dict[str, Any] = {}
    is_active: bool = True


class WorkflowOut(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: Optional[str]
    graph: Dict[str, Any]
    trigger_type: str
    trigger_config: Dict[str, Any]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RunTriggerRequest(BaseModel):
    payload: Dict[str, Any] = {}


class WorkflowRunOut(BaseModel):
    id: int
    workflow_id: int
    status: str
    trigger_payload: Optional[Dict[str, Any]]
    context: Dict[str, Any]
    step_logs: List[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    duration_ms: Optional[int]
    started_at: datetime
    finished_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---------- Lead ----------
class LeadCreate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[str] = "api"
    data: Dict[str, Any] = {}


class LeadOut(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    source: Optional[str]
    status: str
    score: float
    requires_human: bool
    data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Analytics ----------
class AnalyticsResponse(BaseModel):
    total_leads: int
    leads_today: int
    total_runs: int
    success_runs: int
    failed_runs: int
    avg_response_ms: float
    conversion_rate: float
    active_workflows: int
    runs_by_status: Dict[str, int]
    runs_last_7_days: List[Dict[str, Any]]


# ---------- AI ----------
class AIGenerateWorkflowRequest(BaseModel):
    description: str


class AIGenerateWorkflowResponse(BaseModel):
    name: str
    description: str
    graph: Dict[str, Any]
    trigger_type: str
    trigger_config: Dict[str, Any]
