import os, pandas as pd, streamlit as st
from dotenv import load_dotenv
from agents.ingestion_agent import load_eml_folder
from agents.controller_agent import process_batch
from email import policy
from email.parser import BytesParser
from langchain_openai import ChatOpenAI

load_dotenv()
st.set_page_config(page_title="Email Intelligence Agent (Barebones)", layout="centered")
st.title("Email Intelligence Agent — Barebones Starter")

DATA_DIR = "./data"
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_emails")

with st.sidebar:
    st.header("Config")
    st.caption("Set your OPENAI_API_KEY in a local .env file")
    st.write(f"Guardrail: **{os.getenv('ENABLE_GUARDRAIL','True')}**")

tab1, tab2 = st.tabs(["📥 Load & Classify", "📊 Results"])

llm = ChatOpenAI(model=os.getenv("LLM_MODEL","gpt-5"), temperature=0.3)

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
        df = pd.DataFrame([{
            "subject": d.get("subject",""),
            "sender": d.get("from",""),
            "date": d.get("date",""),
            "category": d.get("category",""),
            "guardrail": d.get("guardrail",{}).get("status",""),
        } for d in results])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No results yet.")
