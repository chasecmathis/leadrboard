Write-Host "Running Pytest suite..." -ForegroundColor Cyan

uv run python -m pytest tests/ -v
$pytestExit = $LASTEXITCODE

if ($pytestExit -ne 0) {
    Write-Host "Pytest suite failed." -ForegroundColor Red
    exit 1
}

Write-Host "Pytest suite passed!" -ForegroundColor Green