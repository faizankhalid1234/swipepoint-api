# SwipePoint Django — http://127.0.0.1:8000/
# Run from this folder:  .\runserver.ps1
Set-Location $PSScriptRoot
Write-Host ""
Write-Host "Open: http://127.0.0.1:8000/  (home = JSON API)" -ForegroundColor Cyan
Write-Host "Admin: http://127.0.0.1:8000/admin/  |  Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""
& ".\.venv\Scripts\python.exe" manage.py runserver 8000
