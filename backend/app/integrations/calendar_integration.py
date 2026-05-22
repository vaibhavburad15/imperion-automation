"""Google Calendar integration — create event (with simulation fallback)."""
from typing import Dict, Any
from datetime import datetime, timedelta
from app.integrations.base import BaseIntegration
from app.core.logger import logger


class CalendarIntegration(BaseIntegration):
    provider = "calendar"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        title = config.get("title", f"Meeting with {payload.get('name', 'lead')}")
        start = config.get("start") or (datetime.utcnow() + timedelta(days=1)).isoformat()
        duration_min = int(config.get("duration_min", 30))
        attendees = config.get("attendees") or ([payload["email"]] if payload.get("email") else [])

        # Demo / no-credentials simulation
        if not config.get("credentials_json") or not config.get("calendar_id"):
            logger.info(f"[CAL-SIM] '{title}' at {start} ({duration_min}min) attendees={attendees}")
            return {
                "event_created": True, "simulated": True,
                "title": title, "start": start,
                "duration_min": duration_min, "attendees": attendees,
            }

        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            import json as _json
            creds = Credentials.from_service_account_info(
                _json.loads(config["credentials_json"]),
                scopes=["https://www.googleapis.com/auth/calendar"],
            )
            svc = build("calendar", "v3", credentials=creds, cache_discovery=False)
            end = (datetime.fromisoformat(start) + timedelta(minutes=duration_min)).isoformat()
            event = {
                "summary": title,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end, "timeZone": "UTC"},
                "attendees": [{"email": a} for a in attendees],
            }
            ev = svc.events().insert(calendarId=config["calendar_id"], body=event).execute()
            return {"event_created": True, "event_id": ev.get("id"), "link": ev.get("htmlLink")}
        except Exception:
            logger.exception("Calendar create failed")
            raise
