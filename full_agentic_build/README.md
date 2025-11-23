# Full Agentic Build (v4)

Uses the shared root environment, requirements, and data directory.

## Run (from repo root)

1. Ensure the root venv is set up and requirements installed (`python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt`).
2. Make sure root `.env` is populated (copy `.env.example` if needed) with `OPENAI_API_KEY`, `LLM_MODEL`, etc.
3. Start Streamlit:

   ```powershell
   python -m streamlit run full_agentic_build/ui/streamlit_app.py --server.address=0.0.0.0 --server.port=7860
   ```

4. (Optional) Quick smoke of key deps:

   ```powershell
   .\.venv\Scripts\python.exe -c "import langchain, langchain_openai, openai, chromadb; print('ok')"
   ```

## Data and vectorstore

- Shared data lives at `data/` (root). Set `DATA_DIR` and `VECTOR_DIR` env vars to override; defaults point to `data` and `data/vectorstore` at repo root.

## Docker

Built from the single root `Dockerfile`/`docker-compose.yml`. Example:

```powershell
docker compose up email-agent-full
```

### Notes

- Place `.eml` files in a folder and point the UI to that folder under **Load Emails**.
- Vector index persists under `data/vectorstore`.
- Run the Streamlit UI directly:
  - Default: `streamlit run full_agentic_build/ui/streamlit_app.py`
  - Debug (shows full EmailRecord JSON under previews): `streamlit run full_agentic_build/ui/streamlit_app.py -- --debug`
  - With venv on Windows: `.venv\Scripts\streamlit run full_agentic_build/ui/streamlit_app.py`

## Search and categories

- Use the **Semantic Topic Search** tab to enter a query and set the result limit (validated against env defaults). A dropdown lets you filter results by existing categories.
- Optionally provide a category label to tag matched emails; labels are persisted to the corpus (multi-category supported) and shown in the results summary.
- Results are shown in a single expandable table (subject/sender/date/categories/score); click a subject to reveal full content inline.
- Clearing the vector store and re-running classification re-embeds emails with updated categories; embeddings are upserted by stable IDs to avoid duplicates.

## Testing

- From an activated project venv, run: `python -m pytest full_agentic_build/tests/test_search_service.py` (Windows: `.\.venv\Scripts\python.exe -m pytest ...`).
- To view test printouts, add `-s`. If site-packages plugins interfere (e.g., capture errors), run with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
- A lightweight smoke test checks Streamlit entrypoints with stubbed LLM/vectorstore deps: `python -m pytest full_agentic_build/tests/test_streamlit_smoke.py`.
