# Barebones Starter (GPT‑5, Guardrail + Classification)

Minimal skeleton:
- Load `.eml` files
- Guardrail validation (toggle via `ENABLE_GUARDRAIL`)
- LLM classification

## Run
```powershell
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
```
