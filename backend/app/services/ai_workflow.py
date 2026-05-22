"""AI-assisted workflow generation (bonus feature).

If OPENAI_API_KEY is set, calls the model. Otherwise produces a sensible
heuristic-based workflow so the feature is demoable without keys.
"""
import json
import re
from typing import Dict, Any
from app.core.config import settings
from app.core.logger import logger


SYSTEM_PROMPT = """You are a workflow designer for an automation platform.
Given a user's plain-English description, output a JSON workflow with this shape:
{
  "name": "...",
  "description": "...",
  "trigger_type": "webhook|schedule|manual|lead_created",
  "trigger_config": {},
  "graph": {
    "nodes": [
      {"id":"t1","type":"trigger","label":"...","next":"a1"},
      {"id":"a1","type":"action","label":"...","config":{"provider":"crm|email|slack|sheets|whatsapp|telegram|webhook|calendar","action":"...","..."},"next":"a2"},
      ...
    ]
  }
}
Available integrations: crm (upsert_lead), email (send), slack (send), sheets (append), whatsapp (send),
telegram (send), webhook (send), calendar (create). Use {{var}} placeholders for templating.
Output ONLY valid JSON, no commentary."""


def generate_workflow(description: str) -> Dict[str, Any]:
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": description},
                ],
                temperature=0.3,
            )
            text = resp.choices[0].message.content
            text = re.sub(r"^```json|```$", "", text.strip(), flags=re.MULTILINE).strip()
            return json.loads(text)
        except Exception:
            logger.exception("OpenAI workflow gen failed, falling back to heuristic")

    return _heuristic_workflow(description)


def _heuristic_workflow(description: str) -> Dict[str, Any]:
    """Smart-default generator that scans for keywords."""
    desc = description.lower()
    nodes = [{"id": "t1", "type": "trigger", "label": "Lead Created", "next": "crm1"}]
    nodes.append({
        "id": "crm1", "type": "action", "label": "Save to CRM",
        "config": {"provider": "crm", "action": "upsert_lead"},
        "next": None,
    })
    last_id = "crm1"

    def add(node):
        nonlocal last_id
        nodes[-1]["next"] = node["id"]  # link previous's next
        nodes.append(node)
        last_id = node["id"]

    if "email" in desc or "welcome" in desc or "thank" in desc:
        add({
            "id": "email1", "type": "action", "label": "Send Welcome Email",
            "config": {
                "provider": "email", "action": "send",
                "subject": "Welcome {{name}}!",
                "body": "Hi {{name}}, thanks for reaching out. We'll be in touch shortly.",
            },
            "next": None,
        })
    if "slack" in desc or "notify team" in desc or "alert" in desc:
        add({
            "id": "slack1", "type": "action", "label": "Notify Team on Slack",
            "config": {"provider": "slack", "action": "send",
                       "text": "🔔 New lead: {{name}} <{{email}}>"},
            "next": None,
        })
    if "whatsapp" in desc:
        add({
            "id": "wa1", "type": "action", "label": "WhatsApp Reply",
            "config": {"provider": "whatsapp", "action": "send",
                       "text": "Hi {{name}}, we received your request."},
            "next": None,
        })
    if "telegram" in desc:
        add({
            "id": "tg1", "type": "action", "label": "Telegram Alert",
            "config": {"provider": "telegram", "action": "send",
                       "text": "New lead: {{name}} {{email}}"},
            "next": None,
        })
    if "sheet" in desc or "spreadsheet" in desc:
        add({
            "id": "sh1", "type": "action", "label": "Append to Sheet",
            "config": {"provider": "sheets", "action": "append"},
            "next": None,
        })
    if "meeting" in desc or "calendar" in desc or "schedule" in desc:
        add({
            "id": "cal1", "type": "action", "label": "Schedule Meeting",
            "config": {"provider": "calendar", "action": "create",
                       "title": "Intro call with {{name}}", "duration_min": 30},
            "next": None,
        })

    return {
        "name": (description[:60] or "AI-Generated Workflow").strip(),
        "description": description,
        "trigger_type": "lead_created",
        "trigger_config": {},
        "graph": {"nodes": nodes},
    }
