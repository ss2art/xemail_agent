# --- Cross-platform import fix & dotenv ---
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
env_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.llm_utils import create_llm
from agents.ingestion_agent import load_eml_folder
from agents.controller_agent import process_batch
from agents.semantic_agent import search
from agents.discovery_agent import remember_topic
from services.embeddings_service import get_vectorstore, clear_vectorstore
from services.storage_service import load_corpus, save_corpus, add_items, clear_corpus

# UI descriptor for the entire set of read emails (do not change function names)
COLLECTION_LABEL = os.getenv("MAIL_COLLECTION_LABEL", "Mailbox")

st.set_page_config(page_title="Email Intelligence Agent — Full Build v4", layout="wide")
st.title("📧 Email Intelligence Agent — Full Build v4")

# Sidebar: config and quit controls
with st.sidebar:
    st.header("Config")
    st.caption("Set your OPENAI_API_KEY in a local .env file")
    st.write(f"Guardrail: **{os.getenv('ENABLE_GUARDRAIL','True')}**")
    st.markdown("---")

    # Stats: Emails read, Storage size (vector store), IndexSize, LastProcessed
    def _human_bytes(n: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        s = float(n)
        for u in units:
            if s < 1024.0:
                return f"{s:.1f} {u}"
            s /= 1024.0
        return f"{s:.1f} PB"

    def _dir_size(p: str) -> int:
        if not p or not os.path.exists(p):
            return 0
        total = 0
        for root, _, files in os.walk(p):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total

    def _index_size(vs) -> int:
        try:
            return int(vs._collection.count())  # type: ignore[attr-defined]
        except Exception:
            try:
                data = vs._collection.get(include=["metadatas"])  # type: ignore[attr-defined]
                return len(data.get("ids", []))
            except Exception:
                return 0

    email_count = len(load_corpus())
    vs_dir = os.getenv("VECTOR_DIR", "./data/vectorstore")
    storage_size = _dir_size(vs_dir)
    # Use a lightweight vectorstore instance just for stats
    try:
        _vs_stats = get_vectorstore(vs_dir)
        index_size = _index_size(_vs_stats)
    except Exception:
        index_size = 0

    last_proc = st.session_state.get("last_processed_at") or "—"

    st.markdown("---")

    if "quit_requested" not in st.session_state:
        st.session_state["quit_requested"] = False

    # Single-click quit reveals controls immediately
    clicked_quit = False
    if not st.session_state["quit_requested"]:
        clicked_quit = st.button("Quit")
        if clicked_quit:
            st.session_state["quit_requested"] = True

    if st.session_state["quit_requested"]:
        st.warning("To quit: please close this browser tab/window. To stop the backend server, click 'Stop server' below.")
        if st.button("Stop server"):
            st.info("Shutting down the app shortly...")
            def _delayed_exit(delay=1.0):
                import time, os
                time.sleep(delay)
                try:
                    os._exit(0)
                except Exception:
                    pass
            import threading
            threading.Thread(target=_delayed_exit, args=(1.0,), daemon=True).start()

# Initialize LLM & Vectorstore
try:
    llm = create_llm()
    st.success("✅ LLM initialized")
except Exception as e:
    st.error(f"LLM initialization failed: {e}")
    st.stop()

vector_dir = os.getenv("VECTOR_DIR", "./data/vectorstore")
vectorstore = get_vectorstore(vector_dir)

# Tabs include a maintenance section for clearing data and vector store
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📥 Load Emails", "🤖 Classify & Index", "🔎 Topic Search", "📊 Results", "🧹 Maintenance"])

with tab1:
    st.subheader("Load .eml samples")
    folder = st.text_input("Folder path", value="./data/sample_emails")
    if st.button("Load Files"):
        items = load_eml_folder(folder)
        if items:
            add_items(items)
            st.success(f"Loaded {len(items)} emails into the {COLLECTION_LABEL}.")
            st.rerun()
        else:
            st.warning("No .eml files found.")

with tab2:
    st.subheader("Run Classification Pipeline")
    if st.button(f"Process {COLLECTION_LABEL}"):
        data = load_corpus()
        if not data:
            st.warning(f"{COLLECTION_LABEL} is empty. Load emails first.")
        else:
            results = process_batch(llm, vectorstore, data)
            save_corpus(results)
            st.session_state["last_processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Processed {len(results)} emails.")
            st.rerun()

with tab3:
    st.subheader("Semantic Topic Search")
    query = st.text_input("Enter a topic (e.g., Role Playing Games, Job offer, Promotion)")
    if st.button("Search") and query:
        hits = search(vectorstore, query, k=8)
        if hits:
            st.write([{"meta": h.metadata, "preview": h.page_content[:200]} for h in hits])
            if st.checkbox("Remember this topic for future classifications?"):
                remember_topic(vectorstore, query)
                st.info("Topic remembered.")
        else:
            st.info("No hits yet. Try classifying first.")

with tab4:
    st.subheader(f"{COLLECTION_LABEL} Overview")
    data = load_corpus()
    if data:
        df = pd.DataFrame([{
            "subject": d.get("subject",""),
            "sender": d.get("from",""),
            "date": d.get("date",""),
            "category": d.get("category",""),
            "guardrail": d.get("guardrail",{}).get("status",""),
            "guardrail_reason": ", ".join(d.get("guardrail",{}).get("notes", [])),
            "expired": d.get("temporal",{}).get("status",""),
            "subscription": d.get("subscription",{}).get("is_subscription", False),
        } for d in data])
        st.dataframe(df, width='stretch')
    else:
        st.info("No data yet.")

with tab5:
    st.subheader("Maintenance")
    st.caption("Clear stored emails and vector index. This cannot be undone.")

    # Stats (smaller font) above actions
    def _human_bytes2(n: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        s = float(n)
        for u in units:
            if s < 1024.0:
                return f"{s:.1f} {u}"
            s /= 1024.0
        return f"{s:.1f} PB"

    def _dir_size2(p: str) -> int:
        if not p or not os.path.exists(p):
            return 0
        total = 0
        for root, _, files in os.walk(p):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total

    def _index_size2(vs) -> int:
        try:
            return int(vs._collection.count())  # type: ignore[attr-defined]
        except Exception:
            try:
                data = vs._collection.get(include=["metadatas"])  # type: ignore[attr-defined]
                return len(data.get("ids", []))
            except Exception:
                return 0

    email_count2 = len(load_corpus())
    vs_dir2 = os.getenv("VECTOR_DIR", "./data/vectorstore")
    storage_size2 = _dir_size2(vs_dir2)
    try:
        _vs_stats2 = get_vectorstore(vs_dir2)
        index_size2 = _index_size2(_vs_stats2)
    except Exception:
        index_size2 = 0
    last_proc2 = st.session_state.get("last_processed_at") or "—"

    st.markdown("#### Stats")
    st.caption(f"Emails: {email_count2}")
    st.caption(f"Storage Size: {_human_bytes2(storage_size2)}")
    st.caption(f"Index Size: {index_size2}")
    st.caption(f"Last Processed: {last_proc2}")
    if st.button("Refresh Stats"):
        st.rerun()
    st.markdown("---")

    if "confirm_clear_emails" not in st.session_state:
        st.session_state["confirm_clear_emails"] = False
    if "confirm_clear_vector" not in st.session_state:
        st.session_state["confirm_clear_vector"] = False

    c1, c2 = st.columns(2)
    with c1:
        if not st.session_state["confirm_clear_emails"]:
            if st.button("Clear Emails"):
                st.session_state["confirm_clear_emails"] = True
                st.rerun()
        else:
            st.error("Confirm clearing emails. This cannot be undone.")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("Confirm Clear Emails"):
                    clear_corpus()
                    st.session_state["last_processed_at"] = None
                    st.session_state["confirm_clear_emails"] = False
                    st.success(f"Cleared {COLLECTION_LABEL} data file.")
                    st.rerun()
            with cc2:
                if st.button("Cancel"):
                    st.session_state["confirm_clear_emails"] = False
                    st.info("Cancelled.")
                    st.rerun()
    with c2:
        if not st.session_state["confirm_clear_vector"]:
            if st.button("Clear Vector Store"):
                st.session_state["confirm_clear_vector"] = True
                st.rerun()
        else:
            st.error("Confirm clearing vector store. This cannot be undone.")
            vc1, vc2 = st.columns(2)
            with vc1:
                if st.button("Confirm Clear Vector Store"):
                    current_vs = globals().get("vectorstore")
                    clear_vectorstore(vector_dir, current_vs)
                    try:
                        globals()["vectorstore"] = get_vectorstore(vector_dir)
                        st.success("Vector store cleared and reinitialized.")
                    except Exception as e:
                        st.warning(f"Vector store cleared, but reinit failed: {e}")
                    st.session_state["confirm_clear_vector"] = False
                    st.rerun()
            with vc2:
                if st.button("Cancel"):
                    st.session_state["confirm_clear_vector"] = False
                    st.info("Cancelled.")
                    st.rerun()
