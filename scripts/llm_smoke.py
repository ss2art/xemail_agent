#!/usr/bin/env python3
"""Lightweight LLM smoke test for each subproject.

This script attempts to import `create_llm()` from the given subproject
(`barebones_starter` or `full_agentic_build`) and then calls the first
available invocation method on the LLM (invoke -> transform -> predict -> __call__).

It requires that you run it with the subproject virtualenv Python if you want
to test the runtime environment (recommended). If OPENAI_API_KEY is not set
it will report that and skip making remote requests.
"""
from __future__ import annotations
import argparse
import importlib
import os
import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_llm_for(subproject: str):
    # Prefer to avoid importing modules that may execute network-bound or
    # runtime-sensitive code at import time. Instead, detect presence by
    # file existence and only import when we actually plan to instantiate.
    mod_name = f"{subproject}.utils.llm_utils"
    file_path = ROOT / subproject / 'utils' / 'llm_utils.py'
    if file_path.exists():
        return 'factory-file', mod_name, f"{mod_name}.create_llm"

    # Otherwise return a symbolic class name for later import if needed.
    return 'class-name', 'langchain_openai.ChatOpenAI', 'langchain_openai'


def choose_and_call(llm, prompt: str):
    # Determine preferred invocation method
    order = ['invoke', 'transform', 'predict', '__call__']
    for meth in order:
        if meth == '__call__' and callable(llm):
            try:
                return True, llm(prompt)
            except Exception as e:
                return False, e
        if hasattr(llm, meth):
            try:
                fn = getattr(llm, meth)
                return True, fn(prompt)
            except Exception as e:
                return False, e
    return False, RuntimeError('No usable invocation method found')


def run_for(subproject: str):
    print(f"\n--- Running LLM smoke for: {subproject} ---")
    kind, identifier, source = load_llm_for(subproject)
    print(f"Located LLM descriptor: kind={kind}, id={identifier}")

    key = os.getenv('OPENAI_API_KEY')
    if not key:
        print("OPENAI_API_KEY not set in environment; skipping remote invocation (set it to run full smoke).")
        return 0

    # Instantiate now that we have API key and are willing to import runtime code
    llm = None
    try:
        if kind == 'factory-file':
            mod = importlib.import_module(identifier)
            if hasattr(mod, 'create_llm'):
                llm = mod.create_llm()
            else:
                print(f"Module {identifier} missing create_llm()")
                return 2
        elif kind == 'class-name':
            # identifier like 'langchain_openai.ChatOpenAI'
            parts = identifier.split('.', 1)
            pkg, cls = parts[0], parts[1]
            mod = importlib.import_module(pkg)
            Cls = getattr(mod, cls)
            api_model = os.getenv('LLM_MODEL', None)
            kwargs = {}
            if api_model:
                kwargs['model_name'] = api_model
            llm = Cls(**kwargs)
        else:
            print('Unknown descriptor kind:', kind)
            return 2
    except Exception as e:
        print("Unexpected error while creating LLM:", e)
        traceback.print_exc()
        return 2
    prompt = "Say hello and identify your model name."
    ok, result = choose_and_call(llm, prompt)
    if ok:
        print("Invocation succeeded. Result (truncated):")
        try:
            s = str(result)
            print(s[:1000])
        except Exception:
            print(result)
        return 0
    else:
        print("Invocation failed:")
        traceback.print_exception(type(result), result, result.__traceback__)
        return 3


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--subproject', choices=['barebones_starter', 'full_agentic_build'], help='Run smoke test for the given subproject. If omitted, runs both.')
    args = p.parse_args()

    subs = [args.subproject] if args.subproject else ['barebones_starter', 'full_agentic_build']
    exit_codes = []
    for s in subs:
        try:
            rc = run_for(s)
            exit_codes.append(rc)
        except Exception as e:
            print(f"Unexpected error while testing {s}: {e}")
            traceback.print_exc()
            exit_codes.append(4)

    # return worst exit
    sys.exit(max(exit_codes) if exit_codes else 0)


if __name__ == '__main__':
    main()
