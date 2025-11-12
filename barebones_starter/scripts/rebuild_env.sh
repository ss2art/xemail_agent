#!/bin/bash
echo "====================================="
echo " Rebuild Python Environment (Linux/Mac)"
echo "====================================="

# Remove old virtual environment if exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
python3 -m venv .venv
source .venv/bin/activate

echo "Upgrading pip and setuptools..."
python -m pip install --upgrade pip setuptools wheel

echo "Installing requirements..."
pip install -r requirements.txt

echo "Done!"
echo "To activate later, run:"
echo "    source .venv/bin/activate"
echo "Then start Streamlit with:"
echo "    streamlit run ui/streamlit_app.py"
