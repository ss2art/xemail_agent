#!/bin/bash
echo "====================================="
echo " Rebuild shared Python Environment"
echo "====================================="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
cd "$REPO_ROOT"

# Remove old virtual environment if exists
if [ -d ".venv" ]; then
    echo "Removing existing root virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate

echo "Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing shared requirements..."
pip install -r requirements.txt

echo "Done!"
echo "To activate later, run:"
echo "    source .venv/bin/activate"
echo "Then start Streamlit with:"
echo "    streamlit run barebones_starter/ui/streamlit_app.py"
