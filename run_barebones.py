"""Helper to launch the barebones Streamlit app from repo root."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "barebones_starter" / "ui" / "streamlit_app.py"


def _looks_like_container() -> bool:
    if os.getenv("STREAMLIT_BIND_ADDRESS"):
        return False
    if Path("/.dockerenv").exists():
        return True
    cgroup = Path("/proc/1/cgroup")
    if not cgroup.exists():
        return False
    try:
        content = cgroup.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(token in content for token in ("docker", "kubepods", "containerd"))


def _default_bind_address() -> str:
    override = os.getenv("STREAMLIT_BIND_ADDRESS")
    if override:
        return override
    return "0.0.0.0" if _looks_like_container() else "127.0.0.1"


def _venv_python() -> Path:
    """Prefer the repo's root .venv Python; fall back to current interpreter."""
    script_dir = "Scripts" if os.name == "nt" else "bin"
    candidate = ROOT / ".venv" / script_dir / ("python.exe" if os.name == "nt" else "python")
    return candidate if candidate.exists() else Path(sys.executable)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch the barebones Streamlit app using the repo virtual environment if available.",
    )
    parser.add_argument(
        "--port",
        help="Port for Streamlit (overrides $BAREBONES_PORT or default 8501).",
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

    port = args.port or os.getenv("BAREBONES_PORT", "8501")
    env_headless = os.getenv("STREAMLIT_HEADLESS", "true").lower() not in {"0", "false", "no"}
    headless = env_headless if args.headless is None else args.headless
    bind_address = _default_bind_address()
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP),
        f"--server.address={bind_address}",
        f"--server.port={port}",
    ]
    if headless:
        cmd.append("--server.headless=true")
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
