import os
from langchain_openai import ChatOpenAI

def get_llm():
    model = os.getenv("LLM_MODEL", "gpt-5")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    return ChatOpenAI(model=model, temperature=temperature)
