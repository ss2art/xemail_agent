# Full Agentic Build — v4
# Full Agentic Build — v4

This subproject contains the fuller agentic build (multiple agents, services,
and optional Docker compose). The `requirements.txt` lists the critical
LLM/integration pins used for development; other libraries are intentionally
kept minimal and will be pulled in transitively.

## Quick Start (Windows PowerShell)

1. Change into the subproject directory and create/activate a venv:

	```powershell
	Set-Location 'C:\path\to\xemail_agent\full_agentic_build'
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	```

2. Install the pinned requirements:

	```powershell
	.\.venv\Scripts\python.exe -m pip install -r requirements.txt
	```

3. Add your environment variables to `.env` (copy `.env.example` if present),
	including your OpenAI API key:

	```text
	OPENAI_API_KEY=sk-...
	LLM_MODEL=gpt-5
	```

4. Run quick smoke checks (import tests):

	```powershell
	.\.venv\Scripts\python.exe -c "import langchain, langchain_openai, openai, chromadb; print('ok')"
	```

### Optional: Docker

- If you prefer Docker, there's a `docker-compose.yml` and `Dockerfile`.
  Ensure the environment variables are provided to the container (via `.env`
  or compose overrides) before starting the services.

### Notes

- Place `.eml` files in a folder and point the UI to that folder under **Load Emails**.
- Vector index persists under `data/vectorstore`.
