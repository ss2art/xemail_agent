from typing import Dict

def validate_email(item: Dict) -> Dict:
    notes = []
    raw = item.get("raw", "")
    if not raw:
        return {"status": "REJECTED", "notes": ["Empty email body."]}
    if not item.get("subject"):
        notes.append("Missing subject.")
    if not item.get("from"):
        notes.append("Missing sender.")
    if len(raw) > 500_000:
        notes.append("Email too large (>500KB).")
    status = "OK" if not notes else "WARN"
    return {"status": status, "notes": notes}
