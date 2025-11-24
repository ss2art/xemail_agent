import importlib
import os
import sys
import types

import pytest

# Ensure package imports work when running from repo root
CURR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURR, ".."))
REPO_ROOT = os.path.abspath(os.path.join(ROOT, ".."))
for p in (ROOT, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)


def _patch_llm(monkeypatch):
    """
    Stub ChatOpenAI before importing llm_utils to avoid real network calls.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Dummy LLM class used for assertions.
    """
    # Provide a stub langchain_openai module before importing llm_utils.
    class _DummyLLM:
        """Stub ChatOpenAI replacement that captures args and returns 'ok'."""

        def __init__(self, *args, **kwargs):
            """Record initialization arguments for inspection."""
            self.args = args
            self.kwargs = kwargs

        def __call__(self, *args, **kwargs):
            """Return a static response to mimic LLM behavior."""
            return "ok"

    fake_lco = types.ModuleType("langchain_openai")
    fake_lco.ChatOpenAI = _DummyLLM  # type: ignore[attr-defined]
    sys.modules.setdefault("langchain_openai", fake_lco)

    from utils import llm_utils

    monkeypatch.setattr(llm_utils, "ChatOpenAI", _DummyLLM)
    return _DummyLLM


def _patch_embeddings(monkeypatch):
    """
    Stub embeddings/vectorstore classes to avoid external dependencies.

    Args:
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        Dummy Chroma class used for assertions.
    """
    # Stub embedding/vectorstore dependencies so imports avoid network/disk.
    class _DummyEmbeddings:
        """Stub OpenAIEmbeddings replacement that captures init args."""

        def __init__(self, *args, **kwargs):
            """Track provided embedding args without real network calls."""
            self.args = args
            self.kwargs = kwargs

    class _DummyChroma:
        """Stub Chroma replacement that captures init args without disk use."""

        def __init__(self, *args, **kwargs):
            """Track vector store init args without hitting disk."""
            self.args = args
            self.kwargs = kwargs

    fake_lco = sys.modules.get("langchain_openai")
    if not fake_lco:
        fake_lco = types.ModuleType("langchain_openai")
        sys.modules["langchain_openai"] = fake_lco
    fake_lco.OpenAIEmbeddings = _DummyEmbeddings  # type: ignore[attr-defined]

    fake_chroma = types.ModuleType("langchain_chroma")
    fake_chroma.Chroma = _DummyChroma  # type: ignore[attr-defined]
    sys.modules.setdefault("langchain_chroma", fake_chroma)
    # Also stub community fallback to be safe
    fake_comm = types.ModuleType("langchain_community.vectorstores")
    fake_comm.Chroma = _DummyChroma  # type: ignore[attr-defined]
    sys.modules.setdefault("langchain_community.vectorstores", fake_comm)

    from services import embeddings_service

    monkeypatch.setattr(embeddings_service, "OpenAIEmbeddings", _DummyEmbeddings)
    monkeypatch.setattr(embeddings_service, "Chroma", _DummyChroma)
    return _DummyChroma


@pytest.mark.parametrize(
    "module_path, expect_vectorstore",
    [
        ("full_agentic_build.ui.streamlit_app", True),
        ("barebones_starter.ui.streamlit_app", False),
    ],
)
def test_streamlit_entrypoints_import_with_stubs(monkeypatch, tmp_path, module_path, expect_vectorstore):
    """
    Smoke test to ensure Streamlit entrypoints import with stubbed LLM/vectorstore
    dependencies (no network calls). Verifies llm/vectorstore objects are created.
    """
    pytest.importorskip("streamlit")
    pytest.importorskip("pandas")

    if "dotenv" not in sys.modules:
        fake_dotenv = types.ModuleType("dotenv")
        fake_dotenv.load_dotenv = lambda *args, **kwargs: None  # type: ignore[attr-defined]
        sys.modules["dotenv"] = fake_dotenv

    vector_dir = tmp_path / "vector_smoke"
    monkeypatch.setenv("VECTOR_DIR", str(vector_dir))

    DummyLLM = _patch_llm(monkeypatch)
    DummyChroma = _patch_embeddings(monkeypatch)

    # Force a clean import so top-level execution uses the patched stubs.
    sys.modules.pop(module_path, None)
    mod = importlib.import_module(module_path)
    mod = importlib.reload(mod)

    assert hasattr(mod, "llm"), f"{module_path} should expose llm"
    assert isinstance(getattr(mod.llm, "_llm", None), DummyLLM)

    if expect_vectorstore:
        assert hasattr(mod, "vectorstore"), f"{module_path} should expose vectorstore"
        assert isinstance(mod.vectorstore, DummyChroma)
    else:
        assert not hasattr(mod, "vectorstore"), f"{module_path} should not create a vectorstore"
