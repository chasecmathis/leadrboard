Write-Host "Running Black formatting check..." -ForegroundColor Cyan
uv run black --check ./
$blackExit = $LASTEXITCODE

Write-Host "Running Ruff check..." -ForegroundColor Cyan
uv run ruff check ./
$ruffExit = $LASTEXITCODE

if ($blackExit -ne 0 -or $ruffExit -ne 0) {
    Write-Host "Linting failed." -ForegroundColor Red
    exit 1
}

Write-Host "All linting passed!" -ForegroundColor Green