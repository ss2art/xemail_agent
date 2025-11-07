import os, glob
from email import policy
from email.parser import BytesParser
from typing import List, Dict

def load_eml_folder(folder: str) -> List[Dict]:
    items = []
    for path in glob.glob(os.path.join(folder, "*.eml")):
        with open(path, "rb") as f:
            msg = BytesParser(policy=policy.default).parse(f)
        items.append({
            "path": path,
            "subject": msg.get("subject", ""),
            "from": msg.get("from", ""),
            "to": msg.get("to", ""),
            "date": msg.get("date", ""),
            "raw": msg.as_string()
        })
    return items
