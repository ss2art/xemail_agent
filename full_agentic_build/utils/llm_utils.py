import os
from typing import Any
from langchain_openai import ChatOpenAI


class LLMAdapter:
    def __init__(self, llm: Any):
        self._llm = llm
        if callable(llm):
            self._method = "callable"
        elif hasattr(llm, "predict"):
            self._method = "predict"
        elif hasattr(llm, "invoke"):
            self._method = "invoke"
        elif hasattr(llm, "transform"):
            self._method = "transform"
        elif hasattr(llm, "generate"):
            self._method = "generate"
        else:
            self._method = None

    def __call__(self, prompt_or_messages, **kwargs):
        if self._method == "callable":
            return self._llm(prompt_or_messages, **kwargs)
        if self._method == "predict":
            return self._llm.predict(prompt_or_messages, **kwargs)
        if self._method == "invoke":
            return self._llm.invoke(prompt_or_messages, **kwargs)
        if self._method == "transform":
            res = self._llm.transform(prompt_or_messages, **kwargs)
            try:
                return next(res)
            except TypeError:
                return res
            except StopIteration:
                return None
        if self._method == "generate":
            try:
                return self._llm.generate(prompt_or_messages, **kwargs)
            except Exception as e:
                raise RuntimeError(f"generate() failed: {e}")

        raise RuntimeError("No supported invocation method found on LLM instance")

    def __getattr__(self, name: str):
        return getattr(self._llm, name)


def create_llm():
    """Safely create an OpenAI chat model, auto-retry without unsupported params."""
    model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
    temperature = 0.3
    try:
        llm = ChatOpenAI(model_name=model_name, temperature=temperature)
    except Exception as e:
        msg = str(e).lower()
        if "temperature" in msg or "unsupported_value" in msg:
            print(f"⚠️ Model '{model_name}' does not support temperature. Retrying with defaults.")
            llm = ChatOpenAI(model_name=model_name)
        else:
            print(f"❌ Unexpected error while creating LLM: {e}")
            raise
    adapter = LLMAdapter(llm)
    print(f"✅ LLM initialized: {model_name} (adapter method={adapter._method})")
    return adapter
