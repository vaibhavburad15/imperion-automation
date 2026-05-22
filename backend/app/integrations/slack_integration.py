"""Slack integration via incoming webhook."""
import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.config import settings
from app.core.logger import logger


class SlackIntegration(BaseIntegration):
    provider = "slack"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        webhook = config.get("webhook_url") or settings.SLACK_WEBHOOK_URL
        text = self._render(config.get("text", "🔔 New event: {{name}}"), payload)
        if not webhook:
            logger.info(f"[SLACK-SIM] text={text!r}")
            return {"sent": True, "simulated": True, "text": text}
        with httpx.Client(timeout=10) as c:
            r = c.post(webhook, json={"text": text})
            r.raise_for_status()
        return {"sent": True, "text": text}

    @staticmethod
    def _render(template: str, payload: Dict[str, Any]) -> str:
        out = template
        for k, v in payload.items():
            out = out.replace(f"{{{{{k}}}}}", str(v))
        return out
