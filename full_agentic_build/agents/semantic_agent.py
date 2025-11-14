from typing import List, Dict
from langchain_core.documents import Document

def index_documents(vectorstore, docs: List[Dict]):
    if not docs:
        return
    lang_docs = [Document(page_content=d["content"], metadata=d.get("meta", {})) for d in docs if d.get("content")]
    if lang_docs:
        vectorstore.add_documents(lang_docs)

def search(vectorstore, query: str, k: int = 5):
    if not query:
        return []
    return vectorstore.similarity_search(query, k=k)
