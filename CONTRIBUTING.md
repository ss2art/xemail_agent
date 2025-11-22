# Contributing to xemail_agent

This document explains how to set up a local development environment, run
the verification and smoke tests, and follow the project's commit and PR
conventions.

## Quick setup (shared root environment)

- Use the single root virtual environment for both subprojects:

  ```powershell
  Set-Location 'C:\path\to\xemail_agent'
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  copy .env.example .env   # configure OPENAI_API_KEY / LLM_MODEL
  .\.venv\Scripts\python.exe tools\verify_llm.py
  ```

  Run the UIs from repo root:

  ```powershell
  # Barebones (port 8501)
  .\.venv\Scripts\python.exe -m streamlit run .\barebones_starter\ui\streamlit_app.py --server.port 8501 --server.headless true

  # Full build (port 7860)
  .\.venv\Scripts\python.exe -m streamlit run .\full_agentic_build\ui\streamlit_app.py --server.port 7860 --server.headless true
  ```

## Git hooks (commit message enforcement)

- This repository provides a commit-msg hook in `.githooks/commit-msg` that
  enforces commit messages begin with an explicit issue identifier. To
  enable hooks for a fresh clone run:

  ```bash
  git config core.hooksPath .githooks
  ```

- The hook script is tracked in the repo so collaborators can enable it locally.
  Git itself doesn't auto-enable hooks on clone for security reasons.

Supported commit prefixes
-------------------------

The hook accepts the following identifier styles at the start of the commit message:

- Numeric GitHub issue (recommended for linking to GitHub issues):

  - `Issue #123: short summary`
  - `#123: short summary`

Notes:

- GitHub uses numeric issue numbers (e.g. `#123`). To ensure commits link back
  to GitHub issues automatically, use the numeric `#<number>` form. The hook
  enforces that a recognized issue identifier appears at the start of the
  commit message.

## Commit message format

All commits should start with an issue identifier as shown in the supported
formats above. Keep the first (summary) line short (<= 72 characters), then
add a blank line followed by a more detailed description or a bullet list of
what changed and why.

Examples:

- Link to a GitHub issue:

  Issue #42: fix LLM adapter to call .invoke() when needed

- Use a project-prefixed identifier:

  xm-42: add commit-msg hook that accepts xm- prefixed ids

If your workflow uses a project key (like `xm-123`) include it in the commit
so reviewers can quickly map commits to your internal tracking. If you want
your commit to reference a GitHub issue so that GitHub auto-links the commit
to the issue, use the numeric `#<number>` form.

## Running verification and smoke tests

- `tools/verify_llm.py` is a small diagnostic that
  instantiates the project's LLM (prefers `create_llm()` adapters) and
  attempts multiple invocation patterns. Run it in the corresponding venv to
  validate your environment.

- For UI smoke testing, start the Streamlit app and exercise these flows:
  - Load sample EMLs (the repo contains samples under `data/sample_emails`)
  - Run processing (ingest -> parse -> embed -> index -> semantic search)

## Searching the repository

- Note: automated searches and the tools used during development may include
  files under `.venv/` or other workspace folders by default. These are
  typically library site-packages and not source code you should edit.

- When scanning for code to change, exclude virtualenvs and build artifacts.
  Examples:

  - ripgrep (rg): `rg "pattern" --glob '!**/.venv/**'`
  - git grep: `git grep -n "pattern" -- ':!**/.venv/**'` (or simply run from repo and rely on `.gitignore`)

## Making changes / PRs

- Make small, focused commits. Each commit for this issue must be prefixed as
  described above. Push to `main` after you've tested locally or open a PR.

- Add/update tests or small smoke scripts when you change runtime behavior.

## Troubleshooting

- If you see import errors like `No module named 'langchain_openai'`, check
  that you installed the pinned versions from `requirements.txt` in that
  subproject's venv.

- If you find runtime mismatch (object not callable), prefer the project's
  `create_llm()` in `barebones_starter/utils/llm_utils.py` or `full_agentic_build/utils/llm_utils.py`.

## Contact

- For any uncertainty about a change, open a draft PR describing your plan and
  link to this issue (Issue #1). We'll review and iterate.
