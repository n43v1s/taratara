# scripts/dev.ps1
# Local development startup helper untuk Tara Caraka Ceria.
# Jalankan dari root project: .\scripts\dev.ps1

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv\Scripts\Activate.ps1"

if (-not (Test-Path $Venv)) {
    Write-Host "ERROR: .venv tidak ditemukan. Buat dulu dengan:" -ForegroundColor Red
    Write-Host "  py -3.14 -m venv .venv" -ForegroundColor Yellow
    exit 1
}

Write-Host "Mengaktifkan .venv..." -ForegroundColor Cyan
. $Venv

Write-Host "Menjalankan server di http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Set-Location $Root
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
