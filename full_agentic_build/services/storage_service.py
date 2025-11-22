import os, json
from pathlib import Path
from typing import List, Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
EMAIL_JSON = DATA_DIR / "email_data.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_corpus() -> List[Dict[str, Any]]:
    if not EMAIL_JSON.exists():
        return []
    try:
        with EMAIL_JSON.open("r", encoding="utf-8") as f:
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
    with EMAIL_JSON.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def add_items(new_items: List[Dict]):
    data = load_corpus()
    data.extend(new_items)
    save_corpus(data)


def clear_corpus():
    """Remove the saved email corpus file if present."""
    if EMAIL_JSON.exists():
        try:
            EMAIL_JSON.unlink()
        except Exception:
            pass
