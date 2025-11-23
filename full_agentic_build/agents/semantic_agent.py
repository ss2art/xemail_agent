from typing import List, Dict
from uuid import uuid4
from langchain_core.documents import Document

def index_documents(vectorstore, docs: List[Dict]):
    if not docs:
        return
    lang_docs = []
    doc_ids = []
    for d in docs:
        content = d.get("content")
        if not content:
            continue
        meta = d.get("meta", {}) or {}
        # Prefer stable IDs to upsert and avoid duplicate embeddings
        doc_id = meta.get("id") or meta.get("uid") or str(uuid4())
        lang_docs.append(Document(page_content=content, metadata=meta))
        doc_ids.append(doc_id)
    if lang_docs:
        vectorstore.add_documents(lang_docs, ids=doc_ids)

def search(vectorstore, query: str, k: int = 5):
    if not query:
        return []
    return vectorstore.similarity_search(query, k=k)
