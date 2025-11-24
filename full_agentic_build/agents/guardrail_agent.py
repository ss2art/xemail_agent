"""Lightweight guardrail checks on raw email payloads."""

from typing import Dict

def validate_email(item: Dict) -> Dict:
    """
    Apply basic structural checks to an email dict.

    Args:
        item: Email-like dict containing subject, from, and raw body.

    Returns:
        Dict with guardrail status and notes.
    """
    notes = []
    raw = item.get("raw", "") or ""
    if not raw.strip():
        return {"status": "REJECTED", "notes": ["Empty email body."]}
    if not item.get("subject"):
        notes.append("Missing subject.")
    if not item.get("from"):
        notes.append("Missing sender.")
    if len(raw) > 500_000:
        notes.append("Email too large (>500KB).")
    status = "OK" if not notes else "WARN"
    return {"status": status, "notes": notes}
