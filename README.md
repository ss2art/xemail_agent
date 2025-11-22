# Email Intelligence Agent

- `full_agentic_build/`: complete multi-agent build with embeddings, Chroma, Streamlit UI, and Docker support.
- `barebones_starter/`: minimal Streamlit UI plus guardrail/classification agents.

## Common setup (shared for both builds)

1. Create/activate the single root venv and install shared deps:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
2. Configure environment: copy `.env.example` to `.env` (at repo root) and set your keys (e.g., `OPENAI_API_KEY`, `LLM_MODEL`).
3. Shared data lives under `data/` at the repo root (sample `.eml` files and vectorstore artifacts).

## Run targets (from repo root)

- Barebones UI: `python -m streamlit run barebones_starter/ui/streamlit_app.py --server.port 8501`
- Full build UI: `python -m streamlit run full_agentic_build/ui/streamlit_app.py --server.port 7860`
- Shortcuts: `python run_barebones.py` or `python run_full.py` (respects `STREAMLIT_HEADLESS` env; defaults to headless/auto-open disabled)

## Docker (single image for both)

Build once from the repo root:
```powershell
docker build -t xemail-agent .
```
Use `docker compose up` to run either UI; see `docker-compose.yml` for service names and ports.
