# Tools directory

Operational helpers run from the repo root (use the root `.venv` Python when applicable):

- `create_issues.sh` — Create GitHub issues from a JSON file (default: `data/issues.json`). Flags: `--file PATH`, `--dry-run`, `--continue-on-error`, `--verbose`, `--help`.
- `download_and_extract_enron.py` — Download the Enron archive, extract a subset of mailboxes, and sample messages into `.eml` files. Flags: `--mailboxes`, `--offset`, `--emails`, `--help`.
- `import_test_embeddings.py` — Smoke-test importing `OpenAIEmbeddings` from `langchain` or `langchain_openai`. Flags: `--quiet`, `--help`.
- `llm_smoke.py` — Lightweight LLM invocation check for `barebones_starter` or `full_agentic_build`. Flags: `--subproject`, `--help`.
- `verify_llm.py` — Validates `create_llm()` wiring and runs a short prompt. Flags: `--prompt`, `--model`, `--help`.

Development/CI helper scripts that maintain the repo (hooks, lint runners, rebuilds) live under `scripts/`.
