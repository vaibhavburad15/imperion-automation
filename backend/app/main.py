"""FastAPI entrypoint."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logger import logger
from app.api import auth, workspaces, integrations, workflows, leads, webhooks, analytics, ai
from app.workers.scheduler import start_scheduler

os.makedirs("logs", exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Multi-tenant AI-powered automation, CRM and workflow platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Creating database tables…")
    Base.metadata.create_all(bind=engine)
    logger.info("Starting scheduler…")
    start_scheduler()
    logger.info(f"{settings.APP_NAME} ready.")


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME, "status": "ok",
        "docs": "/docs", "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


# Mount routers
prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=prefix)
app.include_router(workspaces.router, prefix=prefix)
app.include_router(integrations.router, prefix=prefix)
app.include_router(workflows.router, prefix=prefix)
app.include_router(leads.router, prefix=prefix)
app.include_router(webhooks.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(ai.router, prefix=prefix)
