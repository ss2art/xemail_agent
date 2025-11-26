"""Persistent storage helpers for email corpus and UIDs."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union
from uuid import uuid4

from services.email_record import EmailRecord

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", REPO_ROOT / "data"))
EMAIL_JSON = DATA_DIR / "email_data.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_UID_PREFIX = "xm-"

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
    """Convert serialized dicts back into EmailRecord objects when requested."""
    if not as_records:
        return raw_items
    return [EmailRecord.from_dict(item) for item in raw_items]


def load_corpus(as_records: bool = False) -> List[Union[Dict[str, Any], EmailRecord]]:
    """
    Load the persisted email corpus from JSON.

    Args:
        as_records: When True, return EmailRecord objects; otherwise dicts.

    Returns:
        List of email objects or dicts; empty list on error/missing file.
    """
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
    """Persist the corpus items to disk as JSON."""
    serialized = _serialize(items)
    with EMAIL_JSON.open("w", encoding="utf-8") as f:
        json.dump(serialized, f, ensure_ascii=False, indent=2)

def add_items(new_items: Iterable[Union[Dict[str, Any], EmailRecord]]):
    """
    Append new items to the stored corpus, skipping duplicates by uid/message_id.
    Returns a dict with counts: inserted, duplicates, missing_id.
    """
    data = load_corpus()
    existing_ids = {it.get("uid") or it.get("message_id") for it in data if it.get("uid") or it.get("message_id")}
    counts = {"inserted": 0, "duplicates": 0, "missing_id": 0}
    for it in new_items:
        payload: Dict[str, Any]
        if isinstance(it, EmailRecord):
            payload = it.to_dict()
        else:
            payload = dict(it)
        uid = payload.get("uid") or payload.get("message_id")
        if not uid:
            counts["missing_id"] += 1
            continue
        if uid in existing_ids:
            counts["duplicates"] += 1
            continue
        # Preserve provided UID/message_id only; do not auto-generate.
        payload["uid"] = uid
        data.append(payload)
        existing_ids.add(uid)
        counts["inserted"] += 1
    if counts["inserted"]:
        save_corpus(data)
    return counts


def clear_corpus():
    """Remove the saved email corpus file if present."""
    if EMAIL_JSON.exists():
        try:
            EMAIL_JSON.unlink()
        except Exception:
            pass


def ensure_uid(item: Dict[str, Any]) -> str:
    """Assign a UID if missing, preferring message_id; uses temp prefix 'xm-'."""
    uid = item.get("uid") or item.get("message_id")
    if not uid:
        uid = f"{TEMP_UID_PREFIX}{uuid4().hex}"
    item["uid"] = uid
    return uid


def apply_category_label(ids: Iterable[str], category: str) -> bool:
    """
    Apply a category label to emails in the corpus by uid/message_id.
    Returns True if any records were updated.
    """
    if not category:
        return False
    id_set = {i for i in ids if i}
    if not id_set:
        return False

    data = load_corpus()
    updated = False
    for it in data:
        identifier = ensure_uid(it)
        if identifier in id_set:
            cats = it.get("categories") or []
            if category not in cats:
                cats.append(category)
                it["categories"] = cats
            # keep primary category if absent
            it.setdefault("category", category)
            updated = True
    if updated:
        save_corpus(data)
    return updated
