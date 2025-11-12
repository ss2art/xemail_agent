from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

print("🔍 Verifying LLM configuration...\n")

# Load .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

if not api_key:
    print("❌ OPENAI_API_KEY not found. Please check your .env file.")
    raise SystemExit(1)

print(f"✅ Using model: {model_name}")

# Initialize and test
try:
    llm = ChatOpenAI(model=model_name)
    print("⚙️  ChatOpenAI initialized successfully.")
    result = llm.invoke("Say hello and identify your model name.")
    print("\n✅ Test prompt succeeded! Model replied:\n")
    print(result.content)
except Exception as e:
    print(f"\n❌ Verification failed: {e}")
