# --- Cross-platform import fix & dotenv ---
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
env_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)

import streamlit as st
import pandas as pd

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
            st.success(f"Processed {len(results)} emails.")

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
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear Emails"):
            clear_corpus()
            st.success(f"Cleared {COLLECTION_LABEL} data file.")
    with c2:
        if st.button("Clear Vector Store"):
            clear_vectorstore(vector_dir)
            # Reinitialize the vectorstore instance to reflect cleared state
            try:
                globals()["vectorstore"] = get_vectorstore(vector_dir)
                st.success("Vector store cleared and reinitialized.")
            except Exception as e:
                st.warning(f"Vector store cleared, but reinit failed: {e}")
