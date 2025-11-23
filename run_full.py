"""Helper to launch the full Streamlit app from repo root."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "full_agentic_build" / "ui" / "streamlit_app.py"


def _venv_python() -> Path:
    """Prefer the repo's root .venv Python; fall back to current interpreter."""
    script_dir = "Scripts" if os.name == "nt" else "bin"
    candidate = ROOT / ".venv" / script_dir / ("python.exe" if os.name == "nt" else "python")
    return candidate if candidate.exists() else Path(sys.executable)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the full Streamlit app using the repo virtual environment if available.",
    )
    parser.add_argument(
        "--port",
        help="Port for Streamlit (overrides $FULL_PORT or default 7860).",
    )
    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Force Streamlit to run headless.",
    )
    parser.add_argument(
        "--no-headless",
        dest="headless",
        action="store_false",
        help="Disable headless mode even if STREAMLIT_HEADLESS is set.",
    )
    parser.set_defaults(headless=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    args = parse_args(argv)

    # Ensure we run with the repo .venv if present to avoid missing dependencies.
    python = _venv_python()
    if python.resolve() != Path(sys.executable).resolve():
        os.execv(str(python), [str(python), __file__, *argv])

    port = args.port or os.getenv("FULL_PORT", "7860")
    env_headless = os.getenv("STREAMLIT_HEADLESS", "true").lower() not in {"0", "false", "no"}
    headless = env_headless if args.headless is None else args.headless
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP),
        "--server.address=0.0.0.0",
        f"--server.port={port}",
    ]
    if headless:
        cmd.append("--server.headless=true")
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
