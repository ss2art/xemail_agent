import os
try:
    # Preferred: langchain exposes embeddings in some distributions
    from langchain.embeddings import OpenAIEmbeddings  # type: ignore
except Exception:
    # Fallback to the integration package used in this repo's venv
    from langchain_openai import OpenAIEmbeddings  # type: ignore

from langchain.vectorstores import Chroma

def get_embeddings():
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)

def get_vectorstore(persist_directory: str = None):
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    os.makedirs(persist_directory, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)
