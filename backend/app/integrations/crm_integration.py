"""Built-in CRM integration — writes leads to our own database.

This is a 'real' CRM for the platform's purposes (multi-tenant lead store).
Workflows can use it to create/update lead records.
"""
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.database import SessionLocal
from app.models import Lead
from app.core.logger import logger


class CRMIntegration(BaseIntegration):
    provider = "crm"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        ws_id = payload.get("_workspace_id") or config.get("workspace_id")
        db = SessionLocal()
        try:
            if action in ("upsert_lead", "create_lead"):
                email = payload.get("email") or config.get("email")
                existing = None
                if email:
                    existing = db.query(Lead).filter(
                        Lead.workspace_id == ws_id, Lead.email == email
                    ).first()
                if existing:
                    existing.status = config.get("status", existing.status)
                    existing.data = {**(existing.data or {}), **payload}
                    db.commit()
                    return {"lead_id": existing.id, "updated": True}
                lead = Lead(
                    workspace_id=ws_id,
                    name=payload.get("name"),
                    email=email,
                    phone=payload.get("phone"),
                    source=payload.get("source", "workflow"),
                    status=config.get("status", "new"),
                    data=payload,
                )
                db.add(lead)
                db.commit()
                db.refresh(lead)
                return {"lead_id": lead.id, "created": True}
            elif action == "update_status":
                lead_id = payload.get("lead_id") or config.get("lead_id")
                new_status = config.get("status", "contacted")
                lead = db.query(Lead).filter(Lead.id == lead_id,
                                             Lead.workspace_id == ws_id).first()
                if lead:
                    lead.status = new_status
                    db.commit()
                    return {"lead_id": lead.id, "status": new_status}
                return {"error": "lead not found"}
            else:
                raise ValueError(f"CRM action '{action}' not supported")
        finally:
            db.close()
