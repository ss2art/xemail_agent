# Scripts directory

Repo maintenance and local env helpers (run from repository root):

- `clean_rebuild.sh` / `clean_rebuild.ps1` — Recreate the root `.venv` and reinstall `requirements.txt`. Flags: `--help`.
- `enable_hooks.ps1` — Point Git to `.githooks` for this repo (`git config core.hooksPath .githooks`). Flags: `--help`.
- `check_env_and_lint.ps1` — Run `tools/llm_smoke.py` for each subproject using the root virtualenv; runs `ruff check .` when available. Flags: `--help`.

The `barebones_starter/scripts` folder has its own rebuild helper for the shared environment.
