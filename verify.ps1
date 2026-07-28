$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"

function Run-Step {
    param(
        [string] $Name,
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
    & $Command
}

Run-Step "Backend tests" {
    Set-Location $backend
    .\.venv\Scripts\python.exe -m pytest
}

Run-Step "Backend lint" {
    Set-Location $backend
    .\.venv\Scripts\python.exe -m ruff check app tests
}

Run-Step "Frontend typecheck" {
    Set-Location $frontend
    npm.cmd run typecheck
}

Run-Step "Frontend tests" {
    Set-Location $frontend
    npm.cmd test
}

Run-Step "Frontend production build" {
    Set-Location $frontend
    npm.cmd run build
}

Set-Location $root
Write-Host ""
Write-Host "All verification checks completed." -ForegroundColor Green
