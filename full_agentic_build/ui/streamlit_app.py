# --- Cross-platform imports & dotenv ---
import sys, os, json, threading, subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]          # full_agentic_build/
REPO_ROOT = BASE_DIR.parent                             # repo root
sys.path.append(str(BASE_DIR))

from dotenv import load_dotenv
root_env = REPO_ROOT / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env, override=True)

import streamlit as st
import pandas as pd

from utils.llm_utils import create_llm
from agents.ingestion_agent import load_eml_folder
from agents.controller_agent import process_batch
from agents.discovery_agent import remember_topic
from services.embeddings_service import get_vectorstore, clear_vectorstore
from services.storage_service import load_corpus, save_corpus, add_items, clear_corpus
from services.email_markdown import to_markdown
from services.search_service import search_emails, get_limit_defaults

# UI descriptor for the entire set of read emails (do not change function names)
COLLECTION_LABEL = os.getenv("MAIL_COLLECTION_LABEL", "Mailbox")
DATA_DIR = os.getenv("DATA_DIR", str(REPO_ROOT / "data"))
VECTOR_DIR = os.getenv("VECTOR_DIR", str(Path(DATA_DIR) / "vectorstore"))

def _version_label(default: str = "v6") -> str:
    """Resolve app version from env or latest git tag; fall back to default."""
    env_ver = os.getenv("APP_VERSION") or os.getenv("BUILD_TAG")
    if env_ver:
        return env_ver
    try:
        out = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
        tag = out.decode().strip()
        if tag:
            return tag
    except Exception:
        pass
    return default


VERSION = _version_label()
TITLE = f"Email Intelligence Agent - Full Build {VERSION}"
st.set_page_config(page_title=TITLE, layout="wide")
st.title(TITLE)

DEBUG_MODE = "--debug" in sys.argv
# Initialize LLM & Vectorstore
try:
    llm = create_llm()
    st.success("LLM initialized")
except Exception as e:
    st.error(f"LLM initialization failed: {e}")
    st.stop()

vectorstore = get_vectorstore(VECTOR_DIR)
DEFAULT_SEARCH_LIMIT, MAX_SEARCH_LIMIT = get_limit_defaults()


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


def _markdown_from_record(rec: dict) -> str:
    """Reconstruct markdown if not already present."""
    if rec.get("body_markdown"):
        return rec["body_markdown"]
    return to_markdown(
        subject=rec.get("subject", "") or "",
        from_addr=rec.get("from", "") or rec.get("from_addr", "") or "",
        to_addrs=rec.get("to", []) or [],
        date=rec.get("date", "") or "",
        message_id=rec.get("message_id", "") or "",
        body_text=rec.get("body_text") or rec.get("text") or "",
        body_html=rec.get("body_html") or rec.get("raw") or "",
    )


with st.sidebar:
    st.header("Config")
    st.caption("Set your OPENAI_API_KEY in the root .env file")
    st.write(f"Guardrail: **{os.getenv('ENABLE_GUARDRAIL','True')}**")
    st.markdown("---")

    email_count = len(load_corpus())
    storage_size = _dir_size(VECTOR_DIR)
    try:
        index_size = _index_size(vectorstore)
    except Exception:
        index_size = 0
    last_proc = st.session_state.get("last_processed_at") or "n/a"

    st.caption(f"Emails: {email_count}")
    st.caption(f"Storage Size: {_human_bytes(storage_size)}")
    st.caption(f"Index Size: {index_size}")
    st.caption(f"Last Processed: {last_proc}")
    st.markdown("---")

    if "quit_requested" not in st.session_state:
        st.session_state["quit_requested"] = False

    if not st.session_state["quit_requested"]:
        if st.button("Quit"):
            st.session_state["quit_requested"] = True
    else:
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

            threading.Thread(target=_delayed_exit, args=(1.0,), daemon=True).start()

# Tabs include a maintenance section for clearing data and vector store
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Load Emails", "Classify & Index", "Topic Search", "Results", "Maintenance"]
)

with tab1:
    st.subheader("Load .eml samples")
    folder = st.text_input("Folder path", value=os.path.join(DATA_DIR, "sample_emails"))
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
            with st.spinner("Processing emails..."):
                results = process_batch(llm, vectorstore, data)
                save_corpus(results)
                st.session_state["last_processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Processed {len(results)} emails.")
            st.rerun()

with tab3:
    st.subheader("Semantic Topic Search")
    query = st.text_input("Enter a topic (e.g., Role Playing Games, Job offer, Promotion)")
    col_limit, col_category = st.columns(2)
    with col_limit:
        limit = st.number_input(
            "Max results",
            min_value=1,
            max_value=MAX_SEARCH_LIMIT,
            value=DEFAULT_SEARCH_LIMIT,
            step=1,
        )
    with col_category:
        category_label = st.text_input("Optional category label to tag matches")

    if st.button("Search") and query:
        hits = search_emails(vectorstore, query=query, limit=int(limit), category_name=category_label.strip() or None)
        if hits:
            df = pd.DataFrame(
                [
                    {
                        "subject": h.get("subject", ""),
                        "sender": h.get("sender", ""),
                        "date": h.get("date", ""),
                        "category": h.get("category"),
                        "categories": ", ".join(h.get("categories") or []),
                        "applied_category": h.get("applied_category"),
                        "score": h.get("score"),
                        "snippet": h.get("snippet", ""),
                    }
                    for h in hits
                ]
            )
            st.dataframe(df, width="stretch")
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
            "sender": d.get("from","") or d.get("from_addr",""),
            "date": d.get("date",""),
            "category": d.get("category",""),
            "guardrail": d.get("guardrail",{}).get("status",""),
            "guardrail_reason": ", ".join(d.get("guardrail",{}).get("notes", [])),
            "expired": d.get("temporal",{}).get("status",""),
            "subscription": d.get("subscription",{}).get("is_subscription", False),
            "attachments": len(d.get("attachments", [])),
            "folder": d.get("folder",""),
            "uid": d.get("uid",""),
        } for d in data])
        st.dataframe(df, width="stretch")
        with st.expander("Email details preview"):
            idx = st.number_input("Row", min_value=0, max_value=len(data)-1, value=0, step=1)
            rec = data[int(idx)]
            view_mode = st.selectbox("View as", ["Markdown", "Plain Text", "Raw HTML"], index=0)
            header_lines = [
                f"**Subject:** {rec.get('subject','')}",
                f"From: {rec.get('from','') or rec.get('from_addr','')}",
                f"To: {', '.join(rec.get('to', []) or [])}",
                f"Date: {rec.get('date','')}",
                f"Message-ID: {rec.get('message_id','')}",
                f"Folder/UID: {rec.get('folder','')} / {rec.get('uid','')}",
            ]
            if view_mode == "Plain Text":
                body = rec.get("body_text") or rec.get("text") or rec.get("raw","")
                body_content = "\n".join(header_lines + ["", body or ""])
            elif view_mode == "Raw HTML":
                body = rec.get("body_html") or rec.get("raw","")
                body_content = "\n".join(header_lines + ["", body or ""])
            else:
                body = _markdown_from_record(rec)
                body_content = "\n".join(header_lines + ["", body or ""])
            st.code(body_content or "")
            if DEBUG_MODE:
                st.markdown("**Full record (debug):**")
                st.code(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        st.info("No data yet.")

with tab5:
    st.subheader("Maintenance")
    st.caption("Clear stored emails and vector index. This cannot be undone.")

    email_count2 = len(load_corpus())
    storage_size2 = _dir_size(VECTOR_DIR)
    try:
        index_size2 = _index_size(globals().get("vectorstore"))
    except Exception:
        index_size2 = 0
    last_proc2 = st.session_state.get("last_processed_at") or "n/a"

    st.markdown("#### Stats")
    st.caption(f"Emails: {email_count2}")
    st.caption(f"Storage Size: {_human_bytes(storage_size2)}")
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
                    globals()["vectorstore"] = None
                    try:
                        clear_vectorstore(VECTOR_DIR, current_vs)
                        globals()["vectorstore"] = get_vectorstore(VECTOR_DIR)
                        st.success("Vector store cleared and reinitialized.")
                    except Exception as e:
                        st.error(f"Vector store cleanup failed: {e}")
                    finally:
                        st.session_state["confirm_clear_vector"] = False
                        st.rerun()
            with vc2:
                if st.button("Cancel"):
                    st.session_state["confirm_clear_vector"] = False
                    st.info("Cancelled.")
                    st.rerun()
