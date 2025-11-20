import os, json
from typing import List, Dict, Any, Iterable, Union

from services.email_record import EmailRecord

DATA_DIR = os.getenv("DATA_DIR", "./data")
EMAIL_JSON = os.path.join(DATA_DIR, "email_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

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
    if not os.path.exists(EMAIL_JSON):
        return []
    try:
        with open(EMAIL_JSON, "r", encoding="utf-8") as f:
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
    with open(EMAIL_JSON, "w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)

def add_items(new_items: Iterable[Union[Dict[str, Any], EmailRecord]]):
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
