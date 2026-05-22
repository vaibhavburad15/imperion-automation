"""Integration registry — maps provider name to handler class."""
from app.integrations.email_integration import EmailIntegration
from app.integrations.slack_integration import SlackIntegration
from app.integrations.telegram_integration import TelegramIntegration
from app.integrations.webhook_integration import WebhookIntegration
from app.integrations.sheets_integration import SheetsIntegration
from app.integrations.crm_integration import CRMIntegration
from app.integrations.calendar_integration import CalendarIntegration
from app.integrations.whatsapp_integration import WhatsAppIntegration

REGISTRY = {
    "email": EmailIntegration,
    "gmail": EmailIntegration,
    "slack": SlackIntegration,
    "telegram": TelegramIntegration,
    "webhook": WebhookIntegration,
    "sheets": SheetsIntegration,
    "crm": CRMIntegration,
    "calendar": CalendarIntegration,
    "whatsapp": WhatsAppIntegration,
}


def get_integration(provider: str):
    cls = REGISTRY.get(provider.lower())
    if not cls:
        raise ValueError(f"Unknown integration provider: {provider}")
    return cls()
