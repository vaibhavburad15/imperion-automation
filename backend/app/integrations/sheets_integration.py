"""Google Sheets integration — append a row.

For demo / no-credentials mode, falls back to simulated success.
"""
from typing import Dict, Any
from app.integrations.base import BaseIntegration
from app.core.logger import logger


class SheetsIntegration(BaseIntegration):
    provider = "sheets"

    def execute(self, action: str, config: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        sheet_id = config.get("sheet_id")
        worksheet = config.get("worksheet", "Sheet1")
        row = config.get("row") or [
            payload.get("name", ""),
            payload.get("email", ""),
            payload.get("phone", ""),
            payload.get("source", ""),
        ]
        creds_json = config.get("credentials_json")

        if not creds_json or not sheet_id:
            logger.info(f"[SHEETS-SIM] append sheet={sheet_id} row={row}")
            return {"appended": True, "simulated": True, "row": row}

        try:
            import gspread
            from google.oauth2.service_account import Credentials
            import json as _json
            creds = Credentials.from_service_account_info(
                _json.loads(creds_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(sheet_id).worksheet(worksheet)
            sh.append_row(row)
            return {"appended": True, "row": row}
        except Exception as e:
            logger.exception("Sheets append failed")
            raise
