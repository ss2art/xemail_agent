param(
    [Alias('h')][switch]$help
)

if ($help) {
    Write-Host "Usage: .\scripts\clean_rebuild.ps1 [--help|-h]"
    Write-Host ""
    Write-Host "Recreate the root Python virtual environment and install requirements.txt."
    Write-Host "Options:"
    Write-Host "  --help, -h   Show this help message and exit."
    return
}

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
