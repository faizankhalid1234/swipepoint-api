# SwipePoint Django — create migrations (if any) and apply to DB
# Run from this folder:  .\migrate.ps1   (.\ is required in PowerShell)
Set-Location $PSScriptRoot
$py = ".\.venv\Scripts\python.exe"
Write-Host "`n[SwipePoint] Running makemigrations..." -ForegroundColor Cyan
& $py manage.py makemigrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "`n[SwipePoint] Running migrate..." -ForegroundColor Cyan
& $py manage.py migrate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host ""
Write-Host "Done: migrations OK. Database is up to date." -ForegroundColor Green
Write-Host ""
