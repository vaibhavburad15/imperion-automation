"""Generic outbound webhook integration."""
import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration


class WebhookIntegration(BaseIntegration):
    provider = "webhook"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        url = config["url"]
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        body = config.get("body", payload)
        with httpx.Client(timeout=15) as c:
            r = c.request(method, url, json=body, headers=headers)
        return {
            "status_code": r.status_code,
            "response": r.text[:500],
            "ok": r.is_success,
        }
