Write-Host "🧹 Cleaning Python environment..."
if (Test-Path ".venv") {
    Remove-Item -Recurse -Force .venv
    Write-Host "✅ Removed old virtual environment."
}
python -m venv .venv
. .\.venv\Scripts\activate
Write-Host "⚙️ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✅ Environment rebuilt successfully."
