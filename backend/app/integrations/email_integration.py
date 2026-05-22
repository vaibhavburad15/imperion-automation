"""Email / Gmail integration — sends via SMTP."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.config import settings
from app.core.logger import logger


class EmailIntegration(BaseIntegration):
    provider = "email"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if action != "send":
            raise ValueError(f"Email integration does not support action '{action}'")

        to_addr = config.get("to") or payload.get("email")
        subject = self._render(config.get("subject", "Notification"), payload)
        body = self._render(config.get("body", "Hello {{name}}"), payload)

        host = config.get("smtp_host") or settings.SMTP_HOST
        port = config.get("smtp_port") or settings.SMTP_PORT
        user = config.get("smtp_user") or settings.SMTP_USER
        password = config.get("smtp_password") or settings.SMTP_PASSWORD

        if not host or not user:
            # Simulation mode — useful for demos without real SMTP
            logger.info(f"[EMAIL-SIM] to={to_addr} subject={subject!r}")
            return {"sent": True, "simulated": True, "to": to_addr, "subject": subject}

        msg = MIMEMultipart()
        msg["From"] = user
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)

        return {"sent": True, "to": to_addr, "subject": subject}

    @staticmethod
    def _render(template: str, payload: Dict[str, Any]) -> str:
        if not template:
            return ""
        try:
            out = template
            for k, v in payload.items():
                out = out.replace(f"{{{{{k}}}}}", str(v))
            return out
        except Exception:
            return template
