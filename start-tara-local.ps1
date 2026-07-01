param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [string]$PublicUrl = "https://tara.agusrokyanto.com",
    [string]$TunnelName = "tara-caraka-ceria",
    [switch]$Tunnel,
    [switch]$NoReload,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

function Show-Usage {
    Write-Host "Tara Local Web Control Panel starter"
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\start-tara-local.ps1"
    Write-Host "  .\start-tara-local.ps1 -Port 8000"
    Write-Host "  .\start-tara-local.ps1 -Tunnel"
    Write-Host "  .\start-tara-local.ps1 -NoReload"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -HostName    Local bind host. Default: 127.0.0.1"
    Write-Host "  -Port        Local FastAPI port. Default: 8000"
    Write-Host "  -PublicUrl   Public Cloudflare Access URL. Default: https://tara.agusrokyanto.com"
    Write-Host "  -Tunnel      Start cloudflared tunnel in a hidden background process."
    Write-Host "  -TunnelName  Cloudflare tunnel name. Default: tara-caraka-ceria"
    Write-Host "  -NoReload    Start uvicorn without --reload."
    Write-Host "  -Help        Show this help text."
}

if ($Help) {
    Show-Usage
    exit 0
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$DataFolder = Join-Path $Root "data"
$RunsFolder = Join-Path $DataFolder "runs"
$LogsFolder = Join-Path $DataFolder "logs"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Host "ERROR: .venv tidak ditemukan atau belum lengkap." -ForegroundColor Red
    Write-Host "Buat dulu dengan:" -ForegroundColor Yellow
    Write-Host "  py -3.14 -m venv .venv" -ForegroundColor Yellow
    Write-Host "  .\.venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

foreach ($Folder in @($DataFolder, $RunsFolder, $LogsFolder)) {
    if (-not (Test-Path -LiteralPath $Folder)) {
        New-Item -ItemType Directory -Path $Folder | Out-Null
    }
}

$env:APP_ENV = if ([string]::IsNullOrWhiteSpace($env:APP_ENV)) { "development" } else { $env:APP_ENV }
$env:HOST = $HostName
$env:PORT = [string]$Port
$env:PUBLIC_URL = $PublicUrl.TrimEnd("/")
$env:TZ = "Asia/Jakarta"
$env:PYTHONUTF8 = "1"

Set-Location $Root

$PythonVersion = & $VenvPython --version

Write-Host "Starting Tara Local Web Control Panel..."
Write-Host "Root: $Root"
Write-Host "Python: $PythonVersion"
Write-Host "Local URL: http://$HostName`:$Port"
Write-Host "Public URL: $env:PUBLIC_URL"
Write-Host "Data folder: $DataFolder"
Write-Host "Logs folder: $LogsFolder"

if ($Tunnel) {
    $Cloudflared = Get-Command "cloudflared" -ErrorAction SilentlyContinue

    if (-not $Cloudflared) {
        Write-Host "ERROR: cloudflared tidak ditemukan di PATH." -ForegroundColor Red
        Write-Host "Jalankan tanpa -Tunnel, atau install/login cloudflared lebih dulu." -ForegroundColor Yellow
        exit 1
    }

    $TunnelStdout = Join-Path $LogsFolder "cloudflared-tunnel.stdout.log"
    $TunnelStderr = Join-Path $LogsFolder "cloudflared-tunnel.stderr.log"

    Write-Host "Starting Cloudflare tunnel in background..."
    Write-Host "Tunnel name: $TunnelName"
    Write-Host "Tunnel stdout: $TunnelStdout"
    Write-Host "Tunnel stderr: $TunnelStderr"

    $TunnelProcess = Start-Process `
        -FilePath $Cloudflared.Source `
        -ArgumentList @("tunnel", "run", $TunnelName) `
        -WorkingDirectory $Root `
        -WindowStyle Hidden `
        -RedirectStandardOutput $TunnelStdout `
        -RedirectStandardError $TunnelStderr `
        -PassThru

    Write-Host "Cloudflare tunnel PID: $($TunnelProcess.Id)"
}
else {
    Write-Host "Tunnel: disabled. Run with -Tunnel after Cloudflare Access and tunnel config are ready."
}

$UvicornArgs = @(
    "-m",
    "uvicorn",
    "app.main:app",
    "--host",
    $HostName,
    "--port",
    [string]$Port
)

if (-not $NoReload) {
    $UvicornArgs += "--reload"
}

Write-Host "Starting FastAPI..."
Write-Host "Press Ctrl+C to stop the local web server."

& $VenvPython @UvicornArgs
