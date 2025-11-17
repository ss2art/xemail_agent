# --- Cross-platform import fix & dotenv ---
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
env_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)

import streamlit as st
import pandas as pd
from streamlit.components.v1 import html
from utils.llm_utils import create_llm
from agents.ingestion_agent import load_eml_folder
from agents.controller_agent import process_batch
from agents.semantic_agent import search
from agents.discovery_agent import remember_topic
from services.embeddings_service import get_vectorstore
from services.storage_service import load_corpus, save_corpus, add_items

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
    if "close_tab" not in st.session_state:
        st.session_state["close_tab"] = False

    if not st.session_state["quit_requested"]:
        if st.button("Quit"):
            st.session_state["quit_requested"] = True
    else:
        st.warning("To quit: optionally close this tab, then stop the server.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Close this tab"):
                st.session_state["close_tab"] = True
        with col2:
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

        if st.session_state.get("close_tab"):
            html("""
            <script>
                window.open('', '_self');
                window.close();
            </script>
            """)

# Initialize LLM & Vectorstore
try:
    llm = create_llm()
    st.success("✅ LLM initialized")
except Exception as e:
    st.error(f"LLM initialization failed: {e}")
    st.stop()

vector_dir = os.getenv("VECTOR_DIR", "./data/vectorstore")
vectorstore = get_vectorstore(vector_dir)

tab1, tab2, tab3, tab4 = st.tabs(["📥 Load Emails", "🤖 Classify & Index", "🔎 Topic Search", "📊 Results"])

with tab1:
    st.subheader("Load .eml samples")
    folder = st.text_input("Folder path", value="./data/sample_emails")
    if st.button("Load Files"):
        items = load_eml_folder(folder)
        if items:
            add_items(items)
            st.success(f"Loaded {len(items)} emails into corpus.")
        else:
            st.warning("No .eml files found.")

with tab2:
    st.subheader("Run Classification Pipeline")
    if st.button("Process Corpus"):
        data = load_corpus()
        if not data:
            st.warning("Corpus is empty. Load emails first.")
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
    st.subheader("Corpus Overview")
    data = load_corpus()
    if data:
        df = pd.DataFrame([{
            "subject": d.get("subject",""),
            "sender": d.get("from",""),
            "date": d.get("date",""),
            "category": d.get("category",""),
            "guardrail": d.get("guardrail",{}).get("status",""),
            "expired": d.get("temporal",{}).get("status",""),
            "subscription": d.get("subscription",{}).get("is_subscription", False),
        } for d in data])
        st.dataframe(df, use_container_width=True)

        # Show guardrail reasons for failures/warnings
        failed = [d for d in data if d.get("guardrail",{}).get("status") in ("REJECTED","WARN")]
        if failed:
            st.markdown("---")
            st.subheader("Guardrail notes")
            for d in failed:
                subj = d.get("subject","(no subject)")
                status = d.get("guardrail",{}).get("status")
                notes = d.get("guardrail",{}).get("notes", [])
                with st.expander(f"{status}: {subj}"):
                    if notes:
                        for n in notes:
                            st.write(f"- {n}")
                    else:
                        st.write("(no notes)")
    else:
        st.info("No data yet.")
