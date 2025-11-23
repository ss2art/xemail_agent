#!/usr/bin/env python3
"""Probe a virtualenv for files referencing ChatOpenAI (or another needle)."""

import argparse
import os
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parent
    default_site_packages = repo_root / ".venv" / "Lib" / "site-packages"
    parser = argparse.ArgumentParser(
        description="Search site-packages for references to a given string.",
    )
    parser.add_argument(
        "--site-packages",
        type=Path,
        default=default_site_packages,
        help="Path to the site-packages directory to scan.",
    )
    parser.add_argument(
        "--needle",
        default="ChatOpenAI",
        help="String to search for inside .py files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    site_packages = args.site_packages
    if not site_packages.exists():
        print(f"Site-packages not found at {site_packages}")
        return 1

    matches = []
    for dirpath, dirnames, filenames in os.walk(site_packages):
        for fn in filenames:
            if fn.endswith('.py'):
                fp = os.path.join(dirpath, fn)
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        txt = f.read()
                except Exception:
                    continue
                if args.needle in txt:
                    matches.append(fp)
    for match in matches:
        print(match)
    print('found', len(matches), 'matches')
    print('done')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
