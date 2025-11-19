import os, json
from typing import List, Dict, Any

DATA_DIR = os.getenv("DATA_DIR", "./data")
EMAIL_JSON = os.path.join(DATA_DIR, "email_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_corpus() -> List[Dict[str, Any]]:
    if not os.path.exists(EMAIL_JSON):
        return []
    try:
        with open(EMAIL_JSON, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        return json.loads(content)
    except json.JSONDecodeError:
        # Corrupt or partially written file; reset to a clean slate
        clear_corpus()
        return []
    except Exception:
        return []

def save_corpus(items: List[Dict,]):
    with open(EMAIL_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def add_items(new_items: List[Dict]):
    data = load_corpus()
    data.extend(new_items)
    save_corpus(data)


def clear_corpus():
    """Remove the saved email corpus file if present."""
    if os.path.exists(EMAIL_JSON):
        try:
            os.remove(EMAIL_JSON)
        except Exception:
            pass
