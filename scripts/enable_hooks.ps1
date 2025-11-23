# Enable the repository git hooks by setting core.hooksPath
param(
    [Alias('h')][switch]$help
)

if ($help) {
    Write-Output "Usage: .\scripts\enable_hooks.ps1 [--help|-h]"
    Write-Output ""
    Write-Output "Sets git core.hooksPath to .githooks for this repository."
    Write-Output "Options:"
    Write-Output "  --help, -h   Show this help message and exit."
    return
}

Write-Output "Setting git hooks path to .githooks for repository at $(Get-Location)"
git config core.hooksPath .githooks
if ($LASTEXITCODE -eq 0) {
    Write-Output "Done. Hooks enabled."
} else {
    Write-Output "git config returned exit code $LASTEXITCODE"
}
