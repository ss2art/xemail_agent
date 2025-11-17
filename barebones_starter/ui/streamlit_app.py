# --- Path Fix for Cross-Platform Imports ---
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Standard Imports
import os, pandas as pd, streamlit as st, threading, time
from streamlit.components.v1 import html
from agents.ingestion_agent import load_eml_folder
from agents.controller_agent import process_batch
from email import policy
from email.parser import BytesParser
from utils.llm_utils import create_llm



st.set_page_config(page_title="Email Intelligence Agent (Barebones)", layout="centered")
st.title("Email Intelligence Agent — Barebones Starter")

DATA_DIR = "./data"
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_emails")

with st.sidebar:
    st.header("Config")
    st.caption("Set your OPENAI_API_KEY in a local .env file")
    st.write(f"Guardrail: **{os.getenv('ENABLE_GUARDRAIL','True')}**")
    st.markdown("---")
    # Quit controls
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
                    time.sleep(delay)
                    # Use os._exit to ensure the Streamlit process stops cross-platform
                    try:
                        os._exit(0)
                    except Exception:
                        pass
                threading.Thread(target=_delayed_exit, args=(1.0,), daemon=True).start()

        if st.session_state.get("close_tab"):
            html("""
            <script>
                window.open('', '_self');
                window.close();
            </script>
            """)


tab1, tab2 = st.tabs(["📥 Load & Classify", "📊 Results"])

try:
    llm = create_llm()
    st.success("LLM initialized successfully!")
except Exception as e:
    st.error(f"LLM initialization failed: {e}")
    st.stop()

if "corpus" not in st.session_state:
    st.session_state["corpus"] = []
if "results" not in st.session_state:
    st.session_state["results"] = []

with tab1:
    st.subheader("Load .eml samples")
    folder = st.text_input("Folder path", value=SAMPLE_DIR)
    if st.button("Load Files"):
        items = load_eml_folder(folder)
        if items:
            st.session_state["corpus"] = items
            st.success(f"Loaded {len(items)} emails into memory.")
        else:
            st.warning("No .eml files found.")

        if st.button("Run Guardrail + Classification"):
        data = st.session_state.get("corpus", [])
        if not data:
            st.warning("Load emails first.")
        else:
            results = process_batch(llm, data)
            st.session_state["results"] = results
            st.success(f"Processed {len(results)} emails.")


with tab2:
    st.subheader("Results")
    results = st.session_state.get("results", [])
    if results:
        df = pd.DataFrame([
            {
                "subject": r.get("subject",""),
                "sender": r.get("from",""),
                "date": r.get("date",""),
                "category": r.get("category",""),
                "guardrail_status": r.get("guardrail",{}).get("status",""),
            }
            for r in results
        ])
        st.dataframe(df, use_container_width=True)

        # Show guardrail reasons for failures/warnings
        failed = [r for r in results if r.get("guardrail",{}).get("status") in ("REJECTED","WARN")]
        if failed:
            st.markdown("---")
            st.subheader("Guardrail notes")
            for r in failed:
                subj = r.get("subject","(no subject)")
                status = r.get("guardrail",{}).get("status")
                notes = r.get("guardrail",{}).get("notes", [])
                with st.expander(f"{status}: {subj}"):
                    if notes:
                        for n in notes:
                            st.write(f"- {n}")
                    else:
                        st.write("(no notes)")
    else:
        st.info("No results yet. Run classification first.")

