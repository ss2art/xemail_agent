import os, glob
from email import policy
from email.parser import BytesParser
from typing import List, Dict

from services.email_record import EmailRecord, AttachmentRecord
from .parsing_agent import extract_text


def _build_email_record(msg, path: str) -> EmailRecord:
    """Construct an EmailRecord from a parsed email.message.EmailMessage."""
    body = msg.get_body(preferencelist=("html", "plain"))
    body_raw = body.get_content() if body else ""
    content_type = body.get_content_type() if body else ""

    attachments: List[AttachmentRecord] = []
    for part in msg.iter_attachments():
        try:
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                AttachmentRecord(
                    filename=part.get_filename(),
                    content_type=part.get_content_type(),
                    size_bytes=len(payload),
                    is_inline=(part.get_content_disposition() == "inline"),
                    content_id=part.get("Content-ID"),
                )
            )
        except Exception:
            continue

    record = EmailRecord(
        path=path,
        subject=msg.get("subject", ""),
        from_addr=msg.get("from", ""),
        to=msg.get_all("to", []) or [],
        cc=msg.get_all("cc", []) or [],
        bcc=msg.get_all("bcc", []) or [],
        date=msg.get("date", ""),
        message_id=msg.get("message-id", ""),
        headers=dict(msg.items()),
        body_raw=body_raw,
        body_html=body_raw if content_type == "text/html" else None,
        body_text=extract_text(body_raw),
        body_markdown=None,  # placeholder until markdown pipeline lands
        eml_source=path,
        attachments=attachments,
    )
    return record


def _record_to_payload(rec: EmailRecord) -> Dict:
    """Return a dict compatible with existing pipeline expectations."""
    data = rec.to_dict()
    # Legacy keys used elsewhere
    data["from"] = rec.from_addr
    data["raw"] = rec.body_raw
    data["text"] = rec.body_text
    return data


def load_eml_folder(folder: str) -> List[Dict]:
    items = []
    if not folder or not os.path.exists(folder):
        return items
    for path in glob.glob(os.path.join(folder, "*.eml")):
        try:
            with open(path, "rb") as f:
                msg = BytesParser(policy=policy.default).parse(f)
            rec = _build_email_record(msg, path)
            items.append(_record_to_payload(rec))
        except Exception as e:
            items.append({"path": path, "error": str(e)})
    return items
