from typing import List, Dict
from langchain.schema import Document

def index_documents(vectorstore, docs: List[Dict]):
    lang_docs = [Document(page_content=d["content"], metadata=d.get("meta", {})) for d in docs]
    vectorstore.add_documents(lang_docs)

def search(vectorstore, query: str, k: int = 5):
    return vectorstore.similarity_search(query, k=k)
