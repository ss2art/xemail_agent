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
        action="store_true",
        help="Create a git tag v<version> at current HEAD.",
    )
    parser.add_argument(
        "--message",
        default=None,
        help="Commit message when using --commit (default: 'Release vX.Y.Z').",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    version = _validate_version(args.version)

    VERSION_FILE.write_text(f"{version}\n", encoding="utf-8")
    print(f"Wrote {VERSION_FILE} -> {version}")

    if args.commit:
        _run(["git", "add", "VERSION"])
        msg = args.message or f"Release v{version}"
        _run(["git", "commit", "-m", msg])

    if args.tag:
        _run(["git", "tag", f"v{version}"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
