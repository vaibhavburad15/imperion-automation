"""WhatsApp integration via Cloud API (or simulated)."""
import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.logger import logger


class WhatsAppIntegration(BaseIntegration):
    provider = "whatsapp"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        phone_id = config.get("phone_number_id")
        token = config.get("access_token")
        to = config.get("to") or payload.get("phone")
        text = self._render(config.get("text", "Hello {{name}}, thanks for reaching out!"), payload)

        if not phone_id or not token or not to:
            logger.info(f"[WA-SIM] to={to} text={text!r}")
            return {"sent": True, "simulated": True, "to": to, "text": text}

        url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {"messaging_product": "whatsapp", "to": to,
                "type": "text", "text": {"body": text}}
        with httpx.Client(timeout=15) as c:
            r = c.post(url, json=body, headers=headers)
            r.raise_for_status()
        return {"sent": True, "to": to}

    @staticmethod
    def _render(template: str, payload: Dict[str, Any]) -> str:
        out = template
        for k, v in payload.items():
            out = out.replace(f"{{{{{k}}}}}", str(v))
        return out
