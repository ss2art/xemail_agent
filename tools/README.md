# Tools directory

Utilities intended for operational tasks (data downloads, issue helpers, CLI diagnostics). These are run directly with the root `.venv` Python or shell.

- `create_issues.sh`: helper to open GitHub issues from `data/issues.json` (default). Supports labels/projects/assignees. Use `--file PATH` to point at a different JSON file; `--dry-run` prints the `gh issue create` commands without running.

Development/CI helper scripts that maintain the repo (hooks, lint runners, etc.) live under `scripts/`.
