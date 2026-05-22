"""Seed demo data: 2 workspaces, sample workflows, leads.

Run with:  docker compose exec backend python -m app.seed
"""
from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models import Workspace, User, Workflow, Integration, Lead


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Workspace).first():
            print("Seed: data already present, skipping.")
            return

        # ---- Workspace 1: Acme ----
        ws1 = Workspace(name="Acme Corp", slug="acme",
                        settings={"timezone": "Asia/Kolkata"})
        db.add(ws1); db.flush()

        admin1 = User(workspace_id=ws1.id, email="admin@acme.com",
                      full_name="Acme Admin",
                      hashed_password=hash_password("password123"),
                      role="admin")
        db.add(admin1)

        # Integrations for ws1
        db.add(Integration(workspace_id=ws1.id, provider="email",
                           name="Acme Email", config={}))
        db.add(Integration(workspace_id=ws1.id, provider="slack",
                           name="Acme Slack", config={}))
        db.add(Integration(workspace_id=ws1.id, provider="crm",
                           name="Acme CRM", config={}))
        db.add(Integration(workspace_id=ws1.id, provider="sheets",
                           name="Acme Sheets", config={}))
        db.add(Integration(workspace_id=ws1.id, provider="telegram",
                           name="Acme Telegram", config={}))

        # Sample workflow: New lead → CRM → Email welcome → Slack alert
        sample_wf = Workflow(
            workspace_id=ws1.id,
            name="New Lead Onboarding",
            description="Save lead to CRM, send welcome email, notify Slack",
            trigger_type="lead_created",
            graph={
                "nodes": [
                    {"id": "t1", "type": "trigger", "label": "Lead Created", "next": "a1"},
                    {"id": "a1", "type": "action", "label": "Save to CRM",
                     "config": {"provider": "crm", "action": "upsert_lead",
                                "status": "new"}, "next": "c1"},
                    {"id": "c1", "type": "condition", "label": "Needs human?",
                     "config": {"field": "requires_human", "op": "eq", "value": True},
                     "branches": {"true": "slack1", "false": "email1"}},
                    {"id": "email1", "type": "action", "label": "Welcome Email",
                     "config": {"provider": "email", "action": "send",
                                "subject": "Welcome {{name}}!",
                                "body": "Hi {{name}}, thanks for reaching out to Acme. We'll be in touch shortly."},
                     "next": "slack1"},
                    {"id": "slack1", "type": "action", "label": "Slack Alert",
                     "config": {"provider": "slack", "action": "send",
                                "text": "🆕 New lead: {{name}} ({{email}}) score={{score}}"},
                     "next": "fu1"},
                    {"id": "fu1", "type": "follow_up", "label": "Follow-up Email (24h)",
                     "config": {"provider": "email", "action": "send",
                                "subject": "Following up, {{name}}",
                                "body": "Just checking in, {{name}}. Any questions?"},
                     "next": None},
                ]
            },
        )
        db.add(sample_wf)

        # Sample lead
        db.add(Lead(workspace_id=ws1.id, name="Jane Doe",
                    email="jane@example.com", phone="+15551234",
                    source="webform", status="new", score=65.0,
                    data={"company": "Example Inc"}))

        # ---- Workspace 2: Globex ----
        ws2 = Workspace(name="Globex Industries", slug="globex",
                        settings={"timezone": "UTC"})
        db.add(ws2); db.flush()
        db.add(User(workspace_id=ws2.id, email="admin@globex.com",
                    full_name="Globex Admin",
                    hashed_password=hash_password("password123"),
                    role="admin"))
        db.add(Integration(workspace_id=ws2.id, provider="webhook",
                           name="Globex Hook", config={}))

        db.commit()
        print("Seed complete.")
        print("   Login: admin@acme.com / password123  (workspace: acme)")
        print("   Login: admin@globex.com / password123 (workspace: globex)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
