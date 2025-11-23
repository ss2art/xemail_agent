"""
Lightweight checker to ensure OPENAI_API_KEY/LLM_MODEL are configured and the
project-level create_llm() adapters work. Run from repo root:

    python tools/verify_llm.py
"""

import argparse
import importlib
import importlib.util
import os
import traceback
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

SUBPROJECTS = ["full_agentic_build", "barebones_starter"]


def load_create_llm_from(subproject: str):
    """Load create_llm() from a subproject utils module."""
    mod_name = f"{subproject}.utils.llm_utils"
    try:
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "create_llm"):
            return mod.create_llm
    except Exception:
        pass

    # Fallback to loading by file path (works even if not a package)
    file_path = REPO_ROOT / subproject / "utils" / "llm_utils.py"
    if file_path.exists():
        spec = importlib.util.spec_from_file_location(mod_name, str(file_path))
        mod = importlib.util.module_from_spec(spec)
        try:
            assert spec.loader is not None
            spec.loader.exec_module(mod)
            if hasattr(mod, "create_llm"):
                return mod.create_llm
        except Exception:
            pass
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Validate LLM configuration by instantiating create_llm() and exercising common call paths.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--prompt",
        default="Say hello and identify your model name.",
        help="Prompt to send to the LLM during verification.",
    )
    parser.add_argument(
        "--model",
        help="Override the model name instead of using $LLM_MODEL or the default.",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    model_name = args.model or os.getenv("LLM_MODEL", "gpt-4o-mini")

    if not api_key:
        print("ERROR: OPENAI_API_KEY not found. Please populate the root .env file.")
        raise SystemExit(1)

    print(f"Using model: {model_name}")

    create_fn = None
    for sp in SUBPROJECTS:
        create_fn = load_create_llm_from(sp)
        if create_fn:
            print(f"Found create_llm() in {sp}")
            break

    if create_fn is None:
        print("ERROR: No create_llm() adapter found in any subproject.")
        raise SystemExit(1)

    try:
        llm = create_fn()
        print("LLM instantiated successfully.")
    except Exception as e:
        print(f"ERROR: Failed to create or instantiate LLM: {e}")
        traceback.print_exc()
        raise

    prompt = args.prompt

    def try_callable(obj):
        try:
            r = obj(prompt)
            print("\nCallable invocation succeeded. Response:")
            print(r)
            return True
        except Exception as e:
            print("\nCallable invocation failed:", e)
            return False

    def try_predict(obj):
        try:
            if hasattr(obj, "predict"):
                r = obj.predict(prompt)
                print("\npredict() invocation succeeded. Response:")
                print(r)
                return True
        except Exception as e:
            print("\npredict() invocation failed:", e)
        return False

    def try_generate(obj):
        try:
            if hasattr(obj, "generate"):
                try:
                    from langchain.schema import HumanMessage
                except Exception:
                    print("\nSkipping generate() test (langchain.schema.HumanMessage unavailable).")
                    return False
                msgs = [[HumanMessage(content=prompt)]]
                r = obj.generate(msgs)
                print("\ngenerate() invocation succeeded. Raw result:")
                try:
                    gens = getattr(r, "generations", None)
                    if gens:
                        print(gens[0][0])
                    else:
                        print(r)
                except Exception:
                    print(r)
                return True
        except Exception as e:
            print("\ngenerate() invocation failed:", e)
        return False

    def try_invoke(obj):
        try:
            if hasattr(obj, "invoke"):
                r = obj.invoke(prompt)
                print("\ninvoke() invocation succeeded. Response:")
                print(r)
                return True
        except Exception as e:
            print("\ninvoke() invocation failed:", e)
        return False

    def try_transform(obj):
        try:
            if hasattr(obj, "transform"):
                r = obj.transform(prompt)
                print("\ntransform() invocation succeeded. Response:")
                print(r)
                return True
        except Exception as e:
            print("\ntransform() invocation failed:", e)
        return False

    ok = False
    ok = try_callable(llm) or ok
    ok = try_predict(llm) or ok
    ok = try_generate(llm) or ok
    ok = try_invoke(llm) or ok
    ok = try_transform(llm) or ok

    if not ok:
        print("\nERROR: All invocation attempts failed. Attributes on the LLM object:")
        try:
            import inspect
            print([a for a in dir(llm) if not a.startswith('_')])
        except Exception:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
