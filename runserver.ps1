# SwipePoint Django — http://127.0.0.1:8001/
# Run from this folder:  .\runserver.ps1
Set-Location $PSScriptRoot
Write-Host ""
Write-Host "Open: http://127.0.0.1:8001/  (home = JSON API)" -ForegroundColor Cyan
Write-Host "Admin: http://127.0.0.1:8001/admin/  |  Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""
& ".\.venv\Scripts\python.exe" manage.py runserver 8001
