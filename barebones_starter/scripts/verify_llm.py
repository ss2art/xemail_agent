
ii7from dotenv import load_dotenv
import os
import traceback
import importlib
import importlib.util
from pathlib import Path

print("🔍 Verifying LLM configuration...\n")

# Load .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")

if not api_key:
    print("❌ OPENAI_API_KEY not found. Please check your .env file.")
    raise SystemExit(1)

print(f"✅ Using model: {model_name}")

# Initialize: prefer `create_llm()` adapter if available (provides normalized __call__)
llm = None

def load_create_llm_from_subproject(subproject: str):
    """Try to load create_llm from the subproject utils module.

    Attempt normal import first, then fall back to loading the module by
    absolute file path (safe when the package is not a proper importable
    package). Returns the create_llm callable or None.
    """
    mod_name = f"{subproject}.utils.llm_utils"
    try:
        mod = importlib.import_module(mod_name)
        if hasattr(mod, 'create_llm'):
            return mod.create_llm
    except Exception:
        # Try loading by path relative to repo root
        repo_root = Path(__file__).resolve().parents[2]
        file_path = repo_root / subproject / 'utils' / 'llm_utils.py'
        if file_path.exists():
            spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                if hasattr(mod, 'create_llm'):
                    return mod.create_llm
            except Exception:
                pass
    return None

try:
    create_fn = load_create_llm_from_subproject('barebones_starter')
    if create_fn:
        llm = create_fn()
        print("⚙️  Using barebones_starter.utils.create_llm() adapter.")
    else:
        create_fn = load_create_llm_from_subproject('full_agentic_build')
        if create_fn:
            llm = create_fn()
            print("⚙️  Using full_agentic_build.utils.create_llm() adapter.")

    if llm is None:
        # Fail-fast: require a project-provided adapter (`create_llm()`)
        print("❌ No LLM adapter found in the repository (no create_llm()).")
        print("Please run this script from a subproject venv or add a create_llm() factory in the subproject's utils/llm_utils.py.")
        raise SystemExit(1)
except Exception as e:
    print(f"❌ Failed to create or instantiate LLM: {e}")
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

# generate_prompt() tests are skipped because many implementations expect
# a PromptValue-like object (with `.to_messages()`) rather than a bare string.
def try_generate_prompt(obj):
    print('\n⚠️ Skipping generate_prompt() test: this method often requires a PromptValue/to_messages input.')
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
