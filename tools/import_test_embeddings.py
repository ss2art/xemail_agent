#!/usr/bin/env python3
"""Smoke test for importing OpenAIEmbeddings from the expected package."""

import argparse
import sys


def run_imports(quiet: bool) -> int:
    try:
        from langchain.embeddings import OpenAIEmbeddings  # type: ignore

        if not quiet:
            print("OK: imported OpenAIEmbeddings from langchain.embeddings")
        return 0
    except Exception as exc:
        print("ERROR:", type(exc).__name__, exc)

    try:
        from langchain_openai import OpenAIEmbeddings  # type: ignore

        if not quiet:
            print("OK: imported OpenAIEmbeddings from langchain_openai")
        return 0
    except Exception as exc:
        print("ALT ERROR:", type(exc).__name__, exc)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that OpenAIEmbeddings can be imported from either "
            "langchain.embeddings or langchain_openai."
        )
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success messages; only emit errors.",
    )
    args = parser.parse_args(argv)
    return run_imports(args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
