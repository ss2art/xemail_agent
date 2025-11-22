import gc
import os
from pathlib import Path
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

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VECTOR_DIR = Path(os.getenv("VECTOR_DIR") or (REPO_ROOT / "data" / "vectorstore"))


def get_embeddings():
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)


def get_vectorstore(persist_directory: str = None):
    persist_directory = Path(persist_directory or DEFAULT_VECTOR_DIR)
    persist_directory.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    return Chroma(persist_directory=str(persist_directory), embedding_function=embeddings)


def clear_vectorstore(persist_directory: str = None, vectorstore=None):
    """Remove all persisted vectorstore data and recreate the directory."""
    persist_directory = Path(persist_directory or DEFAULT_VECTOR_DIR).resolve()

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

    if persist_directory.is_dir():
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
    persist_directory.mkdir(parents=True, exist_ok=True)
