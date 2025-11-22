"""
download_my_email_to_eml.py
Downloads your OWN emails via IMAP and saves them as .eml files.
"""

import imaplib
import email
import os
import argparse


def download_emails(server, user, password, folder, out_dir, limit):

    os.makedirs(out_dir, exist_ok=True)

    print(f"📡 Connecting to IMAP server: {server}")
    conn = imaplib.IMAP4_SSL(server)
    conn.login(user, password)

    print(f"📂 Selecting folder: {folder}")
    conn.select(folder)

    status, data = conn.search(None, "ALL")
    ids = data[0].split()

    print(f"📊 Found {len(ids)} messages in folder.")

    if limit:
        ids = ids[:limit]

    for i, msg_id in enumerate(ids):
        status, mdata = conn.fetch(msg_id, "(RFC822)")
        raw = mdata[0][1]

        filename = os.path.join(out_dir, f"my_email_{i:05d}.eml")
        with open(filename, "wb") as f:
            f.write(raw)

    conn.logout()
    print(f"✅ Saved {len(ids)} emails into {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, help="IMAP server hostname")
    parser.add_argument("--email", required=True, help="Email username")
    parser.add_argument("--password", required=True, help="IMAP or app password")
    parser.add_argument("--folder", default="INBOX")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--out", default="data/my_emails")

    args = parser.parse_args()

    download_emails(args.server, args.email, args.password,
                    args.folder, args.out, args.limit)
