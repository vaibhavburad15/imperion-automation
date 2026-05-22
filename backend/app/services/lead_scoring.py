"""Simple deterministic lead-scoring + human-handoff logic (bonus feature).

Score is 0-100. Anything >=70 triggers `requires_human=True`.
"""
from typing import Dict, Any


def score_lead(lead_data: Dict[str, Any]) -> float:
    score = 0.0
    email = (lead_data.get("email") or "").lower()
    phone = lead_data.get("phone") or ""
    source = (lead_data.get("source") or "").lower()
    data = lead_data.get("data") or {}

    if email:
        score += 20
        # Business domain is more valuable than free email
        free_domains = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com"}
        domain = email.split("@")[-1] if "@" in email else ""
        if domain and domain not in free_domains:
            score += 15
    if phone:
        score += 15
    if lead_data.get("name"):
        score += 5
    if source in {"referral", "demo_request"}:
        score += 20
    if data.get("budget"):
        try:
            if float(data["budget"]) >= 1000:
                score += 15
        except (TypeError, ValueError):
            pass
    if data.get("company_size"):
        try:
            if int(data["company_size"]) >= 50:
                score += 10
        except (TypeError, ValueError):
            pass

    return min(score, 100.0)


def needs_human_handoff(score: float, lead_data: Dict[str, Any]) -> bool:
    if score >= 70:
        return True
    intent = (lead_data.get("data") or {}).get("intent", "").lower()
    if intent in {"urgent", "buy_now", "demo"}:
        return True
    return False
