#!/usr/bin/env python
"""Update VERSION, optionally commit, and tag the current HEAD."""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION"


def _validate_version(version: str) -> str:
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError("Version must be semver like 0.1.0")
    return version


def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd, cwd=ROOT)


def _current_branch() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None
    branch = out.decode("utf-8", errors="ignore").strip()
    return branch or None


def _version_for_branch(version: str, branch: str | None) -> str:
    base = version.split("-", 1)[0]
    base = _validate_version(base)
    if not branch or branch == "main":
        return base
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "-", branch)
    return f"{base}-{sanitized}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Set repo version and optionally tag.")
    parser.add_argument("version", help="New version (semver, e.g. 0.1.0).")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Create a commit updating VERSION.",
    )
    parser.add_argument(
        "--tag",
        dest="tag",
        action="store_true",
        help="Create a git tag v<version> at current HEAD.",
    )
    parser.add_argument(
        "--no-tag",
        dest="tag",
        action="store_false",
        help="Skip tagging even on main.",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Commit message when using --commit (default: 'Release vX.Y.Z').",
    )
    parser.set_defaults(tag=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    branch = _current_branch()
    version = _version_for_branch(args.version, branch)

    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")
    print(f"Wrote {VERSION_FILE} -> {version}")

    if args.commit:
        _run(["git", "add", "VERSION"])
        msg = args.message or f"Release v{version}"
        has_changes = subprocess.call(
            ["git", "diff", "--cached", "--quiet"],
            cwd=ROOT,
        ) != 0
        if has_changes:
            _run(["git", "commit", "-m", msg])
        else:
            print("No VERSION changes to commit; skipping commit.")

    tag = args.tag
    if tag is None:
        tag = branch == "main"
    if tag:
        if branch and branch != "main":
            raise ValueError("Refusing to tag non-main branch. Checkout main to tag.")
        _run(["git", "tag", f"v{version}"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
