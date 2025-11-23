"""Helpers to persist search topics for later reuse."""

def remember_topic(vectorstore, topic: str):
    """
    Store a topic string in the vector store for future classification runs.

    Args:
        vectorstore: Vector store client supporting add_texts.
        topic: Topic/query text to remember.
    """
    if not topic:
        return
    vectorstore.add_texts([topic], metadatas=[{"type": "topic"}])
