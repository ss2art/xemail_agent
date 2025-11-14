import os, glob
from email import policy
from email.parser import BytesParser
from typing import List, Dict

def load_eml_folder(folder: str) -> List[Dict]:
    items = []
    if not folder or not os.path.exists(folder):
        return items
    for path in glob.glob(os.path.join(folder, "*.eml")):
        try:
            with open(path, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
            raw = msg.get_body(preferencelist=("html","plain"))
            payload = raw.get_content() if raw else ""
            items.append({
                "path": path,
                "subject": msg.get("subject", ""),
                "from": msg.get("from", ""),
                "date": msg.get("date", ""),
                "raw": payload
            })
        except Exception as e:
            items.append({"path": path, "error": str(e)})
    return items
