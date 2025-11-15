# Enable the repository git hooks by setting core.hooksPath
param()

Write-Output "Setting git hooks path to .githooks for repository at $(Get-Location)"
git config core.hooksPath .githooks
if ($LASTEXITCODE -eq 0) {
    Write-Output "Done. Hooks enabled."
} else {
    Write-Output "git config returned exit code $LASTEXITCODE"
}
