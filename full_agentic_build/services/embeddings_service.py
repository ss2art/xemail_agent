import os
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

def get_embeddings():
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    return OpenAIEmbeddings(model=model)

def get_vectorstore(persist_directory: str = None):
    persist_directory = persist_directory or os.getenv("VECTOR_DIR", "./data/vectorstore")
    os.makedirs(persist_directory, exist_ok=True)
    return Chroma(persist_directory=persist_directory, embedding_function=get_embeddings())
