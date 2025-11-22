"""
download_enron_mailboxes_limited.py
-----------------------------------
Downloads the raw Enron dataset (full RFC822 emails)
but extracts ONLY the first N mailboxes for speed.

Then exports emails as .eml files for testing.

Usage:
    python download_enron_mailboxes_limited.py --mailboxes 5 --emails 300
"""

import os
import tarfile
import urllib.request
import email
from email import policy
import random
import argparse
from pathlib import Path

ENRON_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz"


def download_enron(archive_path):
    if os.path.exists(archive_path):
        print("✔ Archive already downloaded.")
        return

    print("📥 Downloading Enron dataset (1.5GB)…")
    urllib.request.urlretrieve(ENRON_URL, archive_path)
    print("✅ Downloaded:", archive_path)


def extract_limited_mailboxes(archive_path, extract_to, mailbox_limit):
    """
    Extract ONLY the first N folders under maildir/<username>
    Example paths (note archive root prefix):
      enron_mail_20110402/maildir/allen-p/
      enron_mail_20110402/maildir/arnold-j/
      …
    """
    print(f"📦 Extracting only first {mailbox_limit} mailboxes…")

    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()

        # Detect archive root prefix (first path part)
        root_prefix = Path(members[0].name).parts[0]
        maildir_prefix = f"{root_prefix}/maildir"

        # Identify top-level maildir folders (root/maildir/<user>/)
        mailboxes = []
        for m in members:
            parts = Path(m.name).parts
            if len(parts) == 3 and parts[0] == root_prefix and parts[1] == "maildir" and m.isdir():
                mailboxes.append(m)

        mailboxes = sorted(mailboxes, key=lambda m: m.name)
        selected = mailboxes[:mailbox_limit]
        if not selected:
            raise RuntimeError("No mailboxes detected in archive; structure may have changed.")

        selected_prefixes = [m.name.rstrip("/") for m in selected]
        print(f"Selected mailboxes: {', '.join(Path(p).name for p in selected_prefixes)}")

        def _filtered():
            for member in members:
                if any(
                    member.name == prefix or member.name.startswith(prefix + "/")
                    for prefix in selected_prefixes
                ):
                    yield member

        tar.extractall(path=extract_to, members=_filtered())

    print("✅ Extracted limited mailboxes.")


def collect_email_files(root):
    """
    Raw Enron maildir emails often have NO extension.
    """
    eml_files = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            # Accept all files without extension (most Enron emails),
            # but also accept .eml or .txt if present
            if "." not in f or f.endswith(".eml") or f.endswith(".txt"):
                eml_files.append(os.path.join(dirpath, f))

    print(f"📊 Found {len(eml_files)} raw email files.")
    return eml_files


def parse_and_save(raw_path, out_dir, index):
    with open(raw_path, "r", encoding="latin-1", errors="ignore") as f:
        raw_text = f.read()

    msg = email.parser.Parser(policy=policy.default).parsestr(raw_text)

    out_file = os.path.join(out_dir, f"email_{index:05d}.eml")
    with open(out_file, "w", encoding="utf-8", errors="ignore") as f:
        f.write(msg.as_string())


def main(mailbox_limit, email_limit):
    archive_path = "data/enron_limited/enron.tgz"
    extract_to = "data/enron_limited/extracted"
    out_dir = "data/enron_sample"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs("data/enron_limited", exist_ok=True)

    # STEP 1 — Download archive
    download_enron(archive_path)

    # STEP 2 — Extract limited number of mailboxes (if missing or empty)
    if (not os.path.exists(extract_to)) or (not os.listdir(extract_to)):
        extract_limited_mailboxes(archive_path, extract_to, mailbox_limit)

    # STEP 3 — Find emails inside extracted maildir
    maildir_root = os.path.join(extract_to, "enron_mail_20110402", "maildir")
    files = collect_email_files(maildir_root)
    sample = random.sample(files, min(email_limit, len(files)))

    print(f"✂️ Sampling {len(sample)} emails…")

    # STEP 4 — Export .eml files
    for i, raw in enumerate(sample):
        parse_and_save(raw, out_dir, i)

    print(f"✅ Saved {len(sample)} emails → {out_dir}")
    print("Done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mailboxes", type=int, default=3,
                        help="Number of user mailboxes to extract.")
    parser.add_argument("--emails", type=int, default=300,
                        help="Number of emails to sample.")
    args = parser.parse_args()

    main(args.mailboxes, args.emails)
