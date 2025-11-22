# Full Agentic Build (v4)

Uses the shared root environment, requirements, and data directory.

## Run (from repo root)

1. Ensure the root venv is set up and requirements installed (`python -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt`).
2. Make sure root `.env` is populated (copy `.env.example` if needed).
3. Start Streamlit:
   ```powershell
   python -m streamlit run full_agentic_build/ui/streamlit_app.py --server.address=0.0.0.0 --server.port=7860
   ```

## Data and vectorstore

- Shared data lives at `data/` (root). Set `DATA_DIR` and `VECTOR_DIR` env vars to override; defaults point to `data` and `data/vectorstore` at repo root.

## Docker

Built from the single root `Dockerfile`/`docker-compose.yml`. Example:
```powershell
docker compose up email-agent-full
```
