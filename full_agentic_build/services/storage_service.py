import os, json
from pathlib import Path
from typing import List, Dict, Any, Iterable, Union

from services.email_record import EmailRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
EMAIL_JSON = DATA_DIR / "email_data.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _serialize(items: Iterable[Union[Dict[str, Any], EmailRecord]]) -> List[Dict[str, Any]]:
    """Ensure items are JSON-serializable dicts."""
    serialized: List[Dict[str, Any]] = []
    for it in items:
        if isinstance(it, EmailRecord):
            serialized.append(it.to_dict())
        else:
            serialized.append(it)
    return serialized


def _deserialize(raw_items: List[Dict[str, Any]], as_records: bool) -> List[Union[Dict[str, Any], EmailRecord]]:
    if not as_records:
        return raw_items
    return [EmailRecord.from_dict(item) for item in raw_items]


def load_corpus(as_records: bool = False) -> List[Union[Dict[str, Any], EmailRecord]]:
    if not EMAIL_JSON.exists():
        return []
    try:
        with EMAIL_JSON.open("r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        data = json.loads(content)
        if not isinstance(data, list):
            return []
        return _deserialize(data, as_records)
    except json.JSONDecodeError:
        # Corrupt or partially written file; reset to a clean slate
        clear_corpus()
        return []
    except Exception:
        return []

def save_corpus(items: Iterable[Union[Dict[str, Any], EmailRecord]]):
    serialized = _serialize(items)
    with EMAIL_JSON.open("w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)

def add_items(new_items: Iterable[Union[Dict[str, Any], EmailRecord]]):
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
