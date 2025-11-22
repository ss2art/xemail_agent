"""Helper to launch the barebones Streamlit app from repo root."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "barebones_starter" / "ui" / "streamlit_app.py"


def _venv_python() -> Path:
    """Prefer the repo's root .venv Python; fall back to current interpreter."""
    script_dir = "Scripts" if os.name == "nt" else "bin"
    candidate = ROOT / ".venv" / script_dir / ("python.exe" if os.name == "nt" else "python")
    return candidate if candidate.exists() else Path(sys.executable)


def main() -> int:
    # Ensure we run with the repo .venv if present to avoid missing dependencies.
    python = _venv_python()
    if python.resolve() != Path(sys.executable).resolve():
        os.execv(str(python), [str(python), __file__, *sys.argv[1:]])

    port = os.getenv("BAREBONES_PORT", "8501")
    headless = os.getenv("STREAMLIT_HEADLESS", "true").lower() not in {"0", "false", "no"}
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
