import os, pandas as pd, streamlit as st
from dotenv import load_dotenv
from agents.ingestion_agent import load_eml_folder
from agents.parsing_agent import extract_text
from agents.controller_agent import process_batch
from agents.semantic_agent import search
from agents.discovery_agent import remember_topic
from services.llm_service import get_llm
from services.embeddings_service import get_vectorstore
from services.storage_service import load_corpus, save_corpus, add_items

load_dotenv()
st.set_page_config(page_title="Email Intelligence Agent", layout="wide")
st.title("Email Intelligence Agent — LLM Classification & Discovery (Full Build)")

DATA_DIR = os.getenv("DATA_DIR", "./data")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_emails")
VECTOR_DIR = os.getenv("VECTOR_DIR", "./data/vectorstore")

with st.sidebar:
    st.header("Config")
    st.caption("Set your OPENAI_API_KEY in a local .env file")
    st.write(f"Guardrail: **{os.getenv('ENABLE_GUARDRAIL','True')}**")

tab1, tab2, tab3, tab4 = st.tabs(["📥 Load Emails", "🤖 Run Classification", "🔎 Topic Search", "📊 Results"])

with tab1:
    st.subheader("Load .eml samples")
    folder = st.text_input("Folder path", value=SAMPLE_DIR)
    if st.button("Load Files"):
        items = load_eml_folder(folder)
        for it in items:
            it["text"] = extract_text(it["raw"])
        if items:
            add_items(items)
            st.success(f"Loaded {len(items)} emails into corpus.")
        else:
            st.warning("No .eml files found.")

with tab2:
    st.subheader("Classify & Index")
    if st.button("Run Classification on Corpus"):
        data = load_corpus()
        if not data:
            st.warning("Corpus is empty. Load emails first.")
        else:
            llm = get_llm()
            vectorstore = get_vectorstore(VECTOR_DIR)
            for d in data:
                if "text" not in d or not d["text"]:
                    d["text"] = extract_text(d.get("raw",""))
            results = process_batch(llm, vectorstore, data)
            save_corpus(results)
            st.success(f"Processed {len(results)} emails.")

with tab3:
    st.subheader("Semantic Topic Search")
    query = st.text_input("Enter a topic (e.g., Role Playing Games, Job offer, Promotion)")
    if st.button("Search") and query:
        vectorstore = get_vectorstore(VECTOR_DIR)
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
    else:
        st.info("No data yet.")
