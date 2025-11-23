"""
download_and_extract_enron.py
-----------------------------
Download the public Enron mail archive, extract a limited number of
mailboxes (with optional offset), and convert a random sample of raw
messages into `.eml` files for local testing.
"""

import argparse
import email
import os
import random
import shutil
import tarfile
import urllib.request
from email import policy
from pathlib import Path

ENRON_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz"


def download_enron(archive_path: Path) -> None:
    if archive_path.exists():
        print("Archive already downloaded.")
        return

    print("Downloading Enron dataset (about 1.5GB)…")
    urllib.request.urlretrieve(ENRON_URL, archive_path)
    print(f"Downloaded archive to {archive_path}")


def extract_limited_mailboxes(
    archive_path: Path,
    temp_extract_dir: Path,
    target_maildir: Path,
    mailbox_limit: int,
    mailbox_offset: int,
) -> None:
    """
    Extract only the requested range of mailboxes from the Enron archive.
    The archive root prefix is preserved temporarily and then flattened
    so the resulting maildir lives under `target_maildir`.
    """
    print(
        f"Extracting {mailbox_limit} mailboxes "
        f"starting at offset {mailbox_offset}…"
    )

    with tarfile.open(archive_path, "r:gz") as tar:
        members = tar.getmembers()
        if not members:
            raise RuntimeError("Archive appears to be empty.")

        root_prefix = Path(members[0].name).parts[0]

        # Identify top-level directories under maildir/<username>/
        mailboxes = []
        for member in members:
            parts = Path(member.name).parts
            if len(parts) == 3 and parts[0] == root_prefix and parts[1] == "maildir" and member.isdir():
                mailboxes.append(member)

        mailboxes.sort(key=lambda m: m.name)
        selected = mailboxes[mailbox_offset: mailbox_offset + mailbox_limit]
        if not selected:
            raise RuntimeError(
                "No mailboxes matched the requested limit/offset. "
                "Try lowering the offset or ensuring the archive is intact."
            )

        selected_prefixes = [m.name.rstrip("/") for m in selected]
        print(
            "Selected mailboxes: "
            + ", ".join(Path(p).name for p in selected_prefixes)
        )

        def filtered():
            for member in members:
                if any(
                    member.name == prefix
                    or member.name.startswith(prefix + "/")
                    for prefix in selected_prefixes
                ):
                    yield member

        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        tar.extractall(path=temp_extract_dir, members=filtered())

    # Flatten: move maildir into the target location
    source_maildir = temp_extract_dir / root_prefix / "maildir"
    if not source_maildir.exists():
        raise RuntimeError(f"Extracted maildir not found at {source_maildir}")

    if target_maildir.exists():
        shutil.rmtree(target_maildir)
    shutil.move(str(source_maildir), str(target_maildir))

    # Remove the leftover root folder
    try:
        shutil.rmtree(temp_extract_dir / root_prefix)
    except FileNotFoundError:
        pass

    print(f"Mailboxes extracted to {target_maildir}")


def collect_email_files(root: Path) -> list[Path]:
    """
    Return a list of paths inside `root` that look like raw emails.
    """
    eml_files: list[Path] = []
    for dirpath, _, files in os.walk(root):
        for filename in files:
            if (
                "." not in filename
                or filename.endswith(".eml")
                or filename.endswith(".txt")
            ):
                eml_files.append(Path(dirpath) / filename)

    print(f"Found {len(eml_files)} raw email files.")
    return eml_files


def parse_and_save(raw_path: Path, out_dir: Path, index: int) -> None:
    with raw_path.open("r", encoding="latin-1", errors="ignore") as handle:
        raw_text = handle.read()

    msg = email.parser.Parser(policy=policy.default).parsestr(raw_text)

    out_file = out_dir / f"email_{index:05d}.eml"
    with out_file.open("w", encoding="utf-8", errors="ignore") as handle:
        handle.write(msg.as_string())


def main(mailbox_limit: int, email_limit: int, mailbox_offset: int) -> None:
    archive_path = Path("data/enron_limited/enron.tgz")
    sample_base = Path("data/enron_sample")
    temp_extract_dir = sample_base / "extracted"
    target_maildir = sample_base / "maildir"
    out_dir = sample_base / "eml"

    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    download_enron(archive_path)

    if not target_maildir.exists() or not any(target_maildir.iterdir()):
        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        extract_limited_mailboxes(
            archive_path,
            temp_extract_dir,
            target_maildir,
            mailbox_limit,
            mailbox_offset,
        )

    mail_files = collect_email_files(target_maildir)
    sample = random.sample(mail_files, min(email_limit, len(mail_files)))

    print(f"Sampling {len(sample)} emails…")
    for idx, raw in enumerate(sample):
        parse_and_save(raw, out_dir, idx)

    print(f"Saved {len(sample)} emails to {out_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Download the Enron mail archive, extract a limited number of "
            "mailboxes, and write a random sample of messages as .eml files."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--mailboxes",
        type=int,
        default=3,
        help="Number of user mailboxes to extract (default: 3).",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Mailbox offset (0 = start at first mailbox, default: 0).",
    )
    parser.add_argument(
        "--emails",
        type=int,
        default=300,
        help="Number of emails to sample across the extracted mailboxes (default: 300).",
    )
    args = parser.parse_args()

    main(args.mailboxes, args.emails, args.offset)
