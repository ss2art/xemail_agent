# Barebones starter README
This subproject contains a minimal Streamlit UI and a small LLM adapter used
for local development and smoke-testing. The requirements file is intentionally
minimal and pins the LangChain/OpenAI integration packages used during testing.

Quick setup (Windows PowerShell)

1. Clone the repo and change directory into this subproject:

	Set-Location 'C:\path\to\xemail_agent\barebones_starter'

2. Create and activate a venv (optional but recommended):

	python -m venv .venv
	.\.venv\Scripts\Activate.ps1

3. Install the minimal runtime requirements:

	.\.venv\Scripts\python.exe -m pip install -r requirements.txt

4. Create a `.env` file (or copy `.env.example` if present) and set your OpenAI API key:

	OPENAI_API_KEY=sk-...
	LLM_MODEL=gpt-5

5. Run the LLM verification script to confirm the environment:

	.\.venv\Scripts\python.exe ..\barebones_starter\scripts\verify_llm.py

6. Run the Streamlit app (headless):

	.\.venv\Scripts\python.exe -m streamlit run .\ui\streamlit_app.py --server.port 8501 --server.headless true

Notes
- The requirements file lists only the critical LLM and runtime packages; most
  other libraries are installed transitively. If you need additional tools for
  development, install them into the venv separately.

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
