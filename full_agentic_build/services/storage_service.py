import os, json
from typing import List, Dict, Any

DATA_DIR = os.getenv("DATA_DIR", "./data")
EMAIL_JSON = os.path.join(DATA_DIR, "email_data.json")
os.makedirs(DATA_DIR, exist_ok=True)

def load_corpus() -> List[Dict[str, Any]]:
    if not os.path.exists(EMAIL_JSON):
        return []
    with open(EMAIL_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def save_corpus(items: List[Dict[str, Any]]):
    with open(EMAIL_JSON, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)

def add_items(new_items: List[Dict[str, Any]]):
    data = load_corpus()
    data.extend(new_items)
    save_corpus(data)
