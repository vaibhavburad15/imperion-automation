"""AI-assisted workflow generation endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models import User
from app.schemas.schemas import AIGenerateWorkflowRequest, AIGenerateWorkflowResponse
from app.services.ai_workflow import generate_workflow

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-workflow", response_model=AIGenerateWorkflowResponse)
def ai_generate_workflow(body: AIGenerateWorkflowRequest,
                         user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    wf = generate_workflow(body.description)
    return AIGenerateWorkflowResponse(**wf)
