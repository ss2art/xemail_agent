import gc
import os
import shutil
import time
from typing import Any
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

# Used to fully tear down Chroma clients between resets
try:  # pragma: no cover - best-effort cleanup on platforms like Windows
    from chromadb.api.shared_system_client import SharedSystemClient
except Exception:  # pragma: no cover
    SharedSystemClient = None  # type: ignore


def get_embeddings():
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)


def get_vectorstore(persist_directory: str = None):
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    os.makedirs(persist_directory, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(persist_directory=persist_directory, embedding_function=embeddings)


def clear_vectorstore(persist_directory: str = None, vectorstore=None):
    """Remove all persisted vectorstore data and recreate the directory."""
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    persist_directory = os.path.abspath(persist_directory)

    def _reset_client(client: Any):
        """Best-effort shutdown to release file handles before deleting the directory."""
        if client is None:
            return
        try:
            client.reset()
        except Exception:
            pass
        try:
            db = getattr(client, "_db", None)
            if db is not None and hasattr(db, "close"):
                db.close()
        except Exception:
            pass
        try:
            # Avoid lingering handles inside HNSW/SQLite on Windows
            system = getattr(client, "_system", None)
            if system is not None and hasattr(system, "stop"):
                system.stop()
        except Exception:
            pass
        try:
            # Clear cached systems so new clients don't reuse stale handles
            if SharedSystemClient is not None:
                # Stop any other cached systems as well
                cache = getattr(SharedSystemClient, "_identifier_to_system", {}) or {}
                for sys_obj in list(cache.values()):
                    try:
                        sys_obj.stop()
                    except Exception:
                        pass
                SharedSystemClient.clear_system_cache()
        except Exception:
            pass

    if vectorstore is not None:
        client = getattr(vectorstore, "_client", None)
        _reset_client(client)

    if os.path.isdir(persist_directory):
        last_error = None
        for attempt in range(5):
            try:
                shutil.rmtree(persist_directory)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.2 * (attempt + 1))
                gc.collect()
        if last_error is not None:
            raise last_error
    os.makedirs(persist_directory, exist_ok=True)
