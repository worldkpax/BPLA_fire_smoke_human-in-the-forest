# Bootstrap Poetry environment (Windows PowerShell)
param(
    [switch]$RuntimeOnly
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Error "Poetry is not installed or not on PATH. Install from https://python-poetry.org/docs/#installation"
    exit 1
}

# Keep the virtualenv inside the project folder for simplicity.
if (-not $env:POETRY_VIRTUALENVS_IN_PROJECT) {
    $env:POETRY_VIRTUALENVS_IN_PROJECT = "1"
}

$installArgs = @("install", "--no-interaction", "--sync")
if (-not $RuntimeOnly) {
    $installArgs += @("--with", "dev")
}

Write-Host "Installing dependencies via Poetry..." -ForegroundColor Cyan
poetry @installArgs

Write-Host "Checking PySide6 WebEngine availability..." -ForegroundColor Cyan
poetry run python -c "from PySide6.QtWebEngineQuick import QtWebEngineQuick; QtWebEngineQuick.initialize(); print('Qt WebEngine ready')"

Write-Host ""
Write-Host "Environment is ready." -ForegroundColor Green
Write-Host "Run GUI: poetry run python -m fire_uav.main"
