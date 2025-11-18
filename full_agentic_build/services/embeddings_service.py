import os
import shutil
try:
    # Preferred embeddings adapter
    from langchain_openai import OpenAIEmbeddings
except Exception:
    from langchain_openai import OpenAIEmbeddings  # type: ignore

# Prefer the new package to avoid deprecation
try:
    from langchain_chroma import Chroma  # type: ignore
except Exception:
    # Fallback for environments without langchain-chroma installed
    from langchain_community.vectorstores import Chroma  # type: ignore


def get_embeddings():
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)


def get_vectorstore(persist_directory: str = None):
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    os.makedirs(persist_directory, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)


def clear_vectorstore(persist_directory: str = None):
    """Remove all persisted vectorstore data and recreate the directory."""
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    if os.path.isdir(persist_directory):
        shutil.rmtree(persist_directory, ignore_errors=True)
    os.makedirs(persist_directory, exist_ok=True)
