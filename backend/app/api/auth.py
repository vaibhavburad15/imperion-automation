"""Auth endpoints — signup creates a new workspace + admin user, login issues JWT."""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models import User, Workspace
from app.schemas.schemas import SignupRequest, LoginRequest, TokenResponse
from app.services.audit import log_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    slug = re.sub(r"[^a-z0-9-]+", "-", body.workspace_name.lower()).strip("-") or "workspace"
    # Ensure unique slug
    base_slug = slug
    i = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        i += 1
        slug = f"{base_slug}-{i}"

    workspace = Workspace(name=body.workspace_name, slug=slug)
    db.add(workspace)
    db.flush()

    user = User(
        workspace_id=workspace.id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    log_audit(db, workspace.id, user.email, "user.signup", "user", user.id)

    token = create_access_token(user.email, workspace_id=workspace.id)
    return TokenResponse(
        access_token=token, workspace_id=workspace.id,
        user_id=user.id, email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "User disabled")
    token = create_access_token(user.email, workspace_id=user.workspace_id)
    return TokenResponse(
        access_token=token, workspace_id=user.workspace_id,
        user_id=user.id, email=user.email,
    )
