"""Load .eml files from disk and normalize into pipeline-ready dicts."""

import glob
import os
from typing import Dict, List

from services.email_parser import parse_email_bytes
from services.email_record import EmailRecord
from services.storage_service import ensure_uid


def _record_to_payload(rec: EmailRecord) -> Dict:
    """Return a dict compatible with existing pipeline expectations."""
    data = rec.to_dict()
    # Legacy keys used elsewhere
    data["from"] = rec.from_addr
    data["raw"] = rec.body_raw
    data["text"] = rec.body_text
    ensure_uid(data)
    return data


def load_eml_folder(folder: str) -> List[Dict]:
    """
    Load all .eml files in the given folder and parse into payload dicts.

    Args:
        folder: Path to a directory containing .eml files.

    Returns:
        List of parsed email payloads or error entries for failures.
    """
    items = []
    if not folder or not os.path.exists(folder):
        return items
    for path in glob.glob(os.path.join(folder, "*.eml")):
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
            rec = parse_email_bytes(raw_bytes, source=path)
            items.append(_record_to_payload(rec))
        except Exception as e:
            items.append({"path": path, "error": str(e)})
    return items
