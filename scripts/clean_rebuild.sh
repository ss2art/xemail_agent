#!/usr/bin/env bash

usage() {
  cat <<'USAGE'
Usage: clean_rebuild.sh [--help|-h]

Recreate the root Python virtual environment and install requirements.txt.

Options:
  --help, -h   Show this help message and exit
USAGE
}

if [[ "${1:-}" =~ ^(--help|-h)$ ]]; then
  usage
  exit 0
fi
if [[ $# -gt 0 ]]; then
  echo "Unknown option: $1" >&2
  usage
  exit 1
fi

echo "🧹 Cleaning Python environment..."
if [ -d ".venv" ]; then
  rm -rf .venv
  echo "✅ Removed old virtual environment."
fi
python3 -m venv .venv
source .venv/bin/activate
echo "⚙️ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Environment rebuilt successfully."
