# Full Agentic Build — v4

Improvements:
- Cross‑platform imports fix
- Explicit `.env` loading
- Safe LLM init via `utils/llm_utils.create_llm()` with temperature fallback
- Requirements pinned to LangChain 0.2.x family (stable with `PromptTemplate`)
- Modular agents + Chroma semantic search
- Docker support

## Quick Start (Windows)
```powershell
copy .env.example .env
# edit .env to add OPENAI_API_KEY
python -m venv .venv
. .\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run ui\streamlit_app.py
```

## Docker
```powershell
docker compose up --build
```

## Notes
- Place `.eml` files in a folder and point the UI to that folder under **Load Emails**.
- Vector index persists under `data/vectorstore`.
