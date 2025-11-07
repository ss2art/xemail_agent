def remember_topic(vectorstore, topic: str):
    vectorstore.add_texts([topic], metadatas=[{"type": "topic"}])
