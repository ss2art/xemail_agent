from dotenv import load_dotenv
import os
import traceback

print("🔍 Verifying LLM configuration...\n")

# Load .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

if not api_key:
    print("❌ OPENAI_API_KEY not found. Please check your .env file.")
    raise SystemExit(1)

print(f"✅ Using model: {model_name}")

# Initialize
try:
    from langchain_openai import ChatOpenAI
except Exception:
    print("❌ Could not import ChatOpenAI from langchain_openai")
    raise

try:
    llm = ChatOpenAI(model_name=model_name)
    print("⚙️  ChatOpenAI initialized successfully.")
except Exception as e:
    print(f"❌ Failed to instantiate ChatOpenAI: {e}")
    traceback.print_exc()
    raise

# Try a few invocation patterns (callable, predict, generate) to be robust across LangChain versions
prompt = "Say hello and identify your model name."

def try_callable(obj):
    try:
        r = obj(prompt)
        print('\n✅ Callable invocation succeeded. Response:')
        print(r)
        return True
    except Exception as e:
        print('\nCallable invocation failed:', e)
        return False

def try_predict(obj):
    try:
        if hasattr(obj, 'predict'):
            r = obj.predict(prompt)
            print('\n✅ predict() invocation succeeded. Response:')
            print(r)
            return True
    except Exception as e:
        print('\npredict() invocation failed:', e)
    return False

def try_generate(obj):
    try:
        # try using message-based generate if available
        try:
            from langchain.schema import HumanMessage
        except Exception:
            print('\n⚠️ langchain.schema.HumanMessage not available; skipping generate() test')
            return False

        if hasattr(obj, 'generate'):
            # many LangChain chat models expect a list of lists of messages
            msgs = [[HumanMessage(content=prompt)]]
            r = obj.generate(msgs)
            print('\n✅ generate() invocation succeeded. Raw result:')
            try:
                # common response shapes
                gens = getattr(r, 'generations', None)
                if gens:
                    print(gens[0][0])
                else:
                    print(r)
            except Exception:
                print(r)
            return True
    except Exception as e:
        print('\ngenerate() invocation failed:', e)
    return False

# Run the checks in order
ok = False
ok = try_callable(llm) or ok
ok = try_predict(llm) or ok
ok = try_generate(llm) or ok

def try_invoke(obj):
    try:
        if hasattr(obj, 'invoke'):
            r = obj.invoke(prompt)
            print('\n✅ invoke() invocation succeeded. Response:')
            print(r)
            return True
    except Exception as e:
        print('\ninvoke() invocation failed:', e)
    return False

def try_generate_prompt(obj):
    try:
        if hasattr(obj, 'generate_prompt'):
            r = obj.generate_prompt(prompt)
            print('\n✅ generate_prompt() invocation succeeded. Response:')
            print(r)
            return True
    except Exception as e:
        print('\ngenerate_prompt() invocation failed:', e)
    return False

def try_transform(obj):
    try:
        if hasattr(obj, 'transform'):
            r = obj.transform(prompt)
            print('\n✅ transform() invocation succeeded. Response:')
            print(r)
            return True
    except Exception as e:
        print('\ntransform() invocation failed:', e)
    return False

ok = try_invoke(llm) or ok
ok = try_generate_prompt(llm) or ok
ok = try_transform(llm) or ok

if not ok:
    print('\n❌ All invocation attempts failed. Listing available attributes on the LLM object:')
    try:
        import inspect
        print([a for a in dir(llm) if not a.startswith('_')])
    except Exception:
        pass
    raise SystemExit(1)
