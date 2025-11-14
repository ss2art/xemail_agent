def remember_topic(vectorstore, topic: str):
    if not topic:
        return
    vectorstore.add_texts([topic], metadatas=[{"type": "topic"}])
