$ErrorActionPreference = "Stop"

Write-Host "MotorMatch - setup & run" -ForegroundColor Cyan

if (!(Test-Path -Path ".\venv")) {
  Write-Host "Creating virtual environment..." -ForegroundColor Yellow
  python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Starting app at http://127.0.0.1:5000" -ForegroundColor Green
python .\main.py

