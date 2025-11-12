#!/usr/bin/env bash
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
