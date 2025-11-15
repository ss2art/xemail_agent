#!/usr/bin/env pwsh
<#
Runs the lightweight llm smoke test in each subproject virtualenv (if present)
and attempts to run `ruff` if available on PATH.

Usage: run from repository root in PowerShell:
  Set-Location 'C:\path\to\xemail_agent'
  .\scripts\check_env_and_lint.ps1
#>

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Write-Output "Repository root: $root"

$subprojects = @('barebones_starter','full_agentic_build')

foreach ($sp in $subprojects) {
    $py = Join-Path $root "$sp\.venv\Scripts\python.exe"
    if (Test-Path $py) {
        Write-Output "\n--- Running llm_smoke for $sp using $py ---"
        & $py (Join-Path $root 'scripts\llm_smoke.py') --subproject $sp
        if ($LASTEXITCODE -ne 0) {
            Write-Output "llm_smoke returned exit code $LASTEXITCODE for $sp"
        }
    } else {
        Write-Output "Skipping $sp: venv python not found at $py"
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
