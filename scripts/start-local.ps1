# SecureCoda Local Services Startup Script (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Starting SecureCoda Development Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
Set-Location $WorkspaceRoot

# 1. Run migrations
Write-Host "`n[1/3] Running database migrations..." -ForegroundColor Yellow
& "$WorkspaceRoot\backend\venv\Scripts\python.exe" "$WorkspaceRoot\backend\manage.py" migrate

# 2. Start Backend Daphne ASGI server in separate window
Write-Host "[2/3] Launching Backend ASGI server on http://localhost:8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$WorkspaceRoot\backend'; & '.\venv\Scripts\python.exe' manage.py runserver 0.0.0.0:8000"

# 3. Start Frontend React development server
Write-Host "[3/3] Launching Frontend React App on http://localhost:3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$WorkspaceRoot\frontend'; npm start"

Write-Host "`nAll services launched successfully!" -ForegroundColor Green
Write-Host "Backend API:  http://localhost:8000/api/" -ForegroundColor Cyan
Write-Host "Frontend App: http://localhost:3000/" -ForegroundColor Cyan
