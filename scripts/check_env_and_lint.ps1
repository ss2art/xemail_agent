#!/usr/bin/env pwsh
<#
Runs the lightweight llm smoke test in each subproject virtualenv (if present)
and attempts to run `ruff` if available on PATH.

Usage: run from repository root in PowerShell:
  Set-Location 'C:\path\to\xemail_agent'
  .\scripts\check_env_and_lint.ps1
#>

param(
    [Alias('h')][switch]$help
)

if ($help) {
    Write-Output "Usage: .\scripts\check_env_and_lint.ps1 [--help|-h]"
    Write-Output ""
    Write-Output "Runs llm_smoke for each subproject using the root virtual environment and optionally runs ruff."
    Write-Output "Options:"
    Write-Output "  --help, -h   Show this help message and exit."
    return
}

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Output "Repository root: $root"

$subprojects = @('barebones_starter','full_agentic_build')
$py = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $py)) {
    Write-Output "Root venv not found at $py; please create it first (python -m venv .venv && pip install -r requirements.txt)."
} else {
    foreach ($sp in $subprojects) {
        Write-Output "\n--- Running llm_smoke for $sp using $py ---"
        & $py (Join-Path $root 'tools\llm_smoke.py') --subproject $sp
        if ($LASTEXITCODE -ne 0) {
            Write-Output "llm_smoke returned exit code $LASTEXITCODE for $sp"
        }
    }
}

# Optional lint step: run ruff if available
try {
    $ruff = (Get-Command ruff -ErrorAction Stop).Source
    Write-Output "\nRunning ruff linting (via $ruff)"
    ruff check .
} catch {
    Write-Output "\nruff not found on PATH; skipping lint step. To run lint locally, install ruff in your environment or use the project's preferred linter."
}
