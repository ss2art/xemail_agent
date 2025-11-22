FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/app/data \
    VECTOR_DIR=/app/data/vectorstore \
    STREAMLIT_SERVER_PORT=7860

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Default to the full build UI; override the command in compose to run barebones.
CMD ["streamlit", "run", "full_agentic_build/ui/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=7860"]
