# Full Agentic Build (LangChain + GPT‑5 + Chroma)

**Features**
- 8 agents (ingestion, guardrail, parsing, classification, temporal, subscription, semantic, discovery).
- Chroma vector store for semantic search and topic memory.
- Streamlit dashboard with tabs for Load, Classify, Search, Results.
- Docker + Compose for deployment.

## Run (Windows 11)
```powershell
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
streamlit run ui/streamlit_app.py
```

## Docker
```powershell
docker compose up --build
```
Open: http://localhost:8501

## Deployment
- **Hugging Face Spaces (Docker Space)**: push this folder with Dockerfile.
- **AWS App Runner**: build & push image to ECR, point App Runner to it.

## Config
- `.env`: `OPENAI_API_KEY`, `ENABLE_GUARDRAIL`, `LLM_MODEL`, `EMBEDDING_MODEL`.
- Vector data persists in `data/vectorstore`.
