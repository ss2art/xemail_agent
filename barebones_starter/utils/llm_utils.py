import os
from langchain_openai import ChatOpenAI

def create_llm():
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature = 0.3

    restricted_models = ["o1", "4.1", "reasoning", "gpt-5"]

    try:
        if any(x in model_name for x in restricted_models):
            llm = ChatOpenAI(model=model_name)
        else:
            llm = ChatOpenAI(model=model_name, temperature=temperature)
    except TypeError as e:
        if "proxies" in str(e):
            print("⚠️ 'proxies' argument no longer supported. Removing and retrying.")
            llm = ChatOpenAI(model=model_name)
        else:
            raise
    except Exception as e:
        print(f"❌ Unexpected error while creating LLM: {e}")
        raise

    print(f"✅ LLM initialized: {model_name}")
    return llm
