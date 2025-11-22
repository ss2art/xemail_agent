# Barebones Starter

Minimal Streamlit UI plus guardrail/classification agents, reusing the shared root environment and data.

## Run (from repo root)

1. Ensure the root venv is ready and requirements installed:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
2. Populate the root `.env` (copy `.env.example` if needed) with `OPENAI_API_KEY` and `LLM_MODEL`.
3. Launch the UI:
   ```powershell
   python -m streamlit run barebones_starter/ui/streamlit_app.py --server.address=0.0.0.0 --server.port=8501
   ```

## Data

- Sample `.eml` files live under the shared `data/sample_emails` directory at repo root. Set `DATA_DIR` to override.
