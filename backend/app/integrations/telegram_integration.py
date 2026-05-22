"""Telegram integration via Bot API."""
import httpx
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.config import settings
from app.core.logger import logger


class TelegramIntegration(BaseIntegration):
    provider = "telegram"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        token = config.get("bot_token") or settings.TELEGRAM_BOT_TOKEN
        chat_id = config.get("chat_id") or settings.TELEGRAM_CHAT_ID
        text = self._render(config.get("text", "New event: {{name}}"), payload)
        if not token or not chat_id:
            logger.info(f"[TG-SIM] chat={chat_id} text={text!r}")
            return {"sent": True, "simulated": True, "text": text}
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        with httpx.Client(timeout=10) as c:
            r = c.post(url, json={"chat_id": chat_id, "text": text})
            r.raise_for_status()
        return {"sent": True, "text": text}

    @staticmethod
    def _render(template: str, payload: Dict[str, Any]) -> str:
        out = template
        for k, v in payload.items():
            out = out.replace(f"{{{{{k}}}}}", str(v))
        return out
