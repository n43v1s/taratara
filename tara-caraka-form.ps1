# tara-caraka-form.ps1
# Scheduler script untuk submit Google Form pendaftaran Tara Caraka Ceria.
#
# Usage:
#   .\tara-caraka-form.ps1 -Mode DryRun
#   .\tara-caraka-form.ps1 -Mode Submit -RunId "run-20260627-120000-abc123"

param(
    [ValidateSet("DryRun", "Submit")]
    [string]$Mode = "DryRun",

    [string]$RunId = "",

    # Optional override: comma-separated attempt times, e.g. "13:00:30,13:00:31"
    [string]$AttemptTimesOverride = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$DataDir     = Join-Path $ScriptDir "data"
$ConfigFile  = Join-Path $DataDir "tara-caraka-form.config.json"
$ProfileFile = Join-Path $DataDir "form-profile.json"
$RunsDir     = Join-Path $DataDir "runs"
$LogsDir     = Join-Path $DataDir "logs"
$LockFile    = Join-Path $DataDir "scheduler.lock"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
function Write-Log {
    param([string]$Message)
    $ts   = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    $line = "[$ts] $Message"
    Write-Host $line
    if ($script:LogFile) {
        Add-Content -Path $script:LogFile -Value $line -Encoding UTF8
    }
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "File tidak ditemukan: $Path"
    }
    return Get-Content -Path $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function New-RunId {
    $ts    = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $short = [System.Guid]::NewGuid().ToString().Substring(0, 6)
    return "run-$ts-$short"
}

# ---------------------------------------------------------------------------
# Main - wrapped in try/catch/finally so window never auto-closes
# ---------------------------------------------------------------------------
$script:LogFile   = $null
$script:ExitCode  = 0

try {

    # Init run
    if (-not $RunId) { $RunId = New-RunId }

    $null = New-Item -ItemType Directory -Force -Path $LogsDir
    $null = New-Item -ItemType Directory -Force -Path $RunsDir

    $script:LogFile = Join-Path $LogsDir "$RunId.log"

    Write-Log "============================================"
    Write-Log "Tara Caraka Ceria -- $Mode"
    Write-Log "Run ID : $RunId"
    Write-Log "============================================"

    # Load config and profile
    Write-Log "Membaca config..."
    $Config  = Read-JsonFile -Path $ConfigFile
    $Profile = Read-JsonFile -Path $ProfileFile

    $ResponseUrl = $Profile.responseUrl
    $Fbzx        = $Profile.fbzx
    $Mappings    = $Profile.mappings

    if (-not $ResponseUrl) {
        throw "responseUrl kosong. Parse Google Form terlebih dahulu."
    }

    Write-Log "Response URL : $ResponseUrl"
    Write-Log "fbzx         : $Fbzx"

    # Build payload
    Write-Log "Membangun payload..."

    $BodyParts = [System.Collections.Generic.List[string]]::new()

    foreach ($InternalField in $Mappings.PSObject.Properties.Name) {
        $EntryId = $Mappings.$InternalField
        $Value   = $Config.$InternalField

        if ($null -eq $Value) { continue }

        $isArray = ($Value -is [System.Array]) -or ($Value -is [System.Collections.IEnumerable] -and $Value -isnot [string])

        if ($isArray) {
            foreach ($v in $Value) {
                $enc = [System.Uri]::EscapeDataString([string]$v)
                $BodyParts.Add("${EntryId}=${enc}")
                Write-Log "  $EntryId = $v"
            }
        } else {
            $enc = [System.Uri]::EscapeDataString([string]$Value)
            $BodyParts.Add("${EntryId}=${enc}")
            Write-Log "  $EntryId = $Value"
        }
    }

    if ($Fbzx) {
        $enc = [System.Uri]::EscapeDataString([string]$Fbzx)
        $BodyParts.Add("fbzx=${enc}")
    }

    $BodyString = [string]::Join("&", $BodyParts)

    # -------------------------------------------------------------------------
    # Dry-run
    # -------------------------------------------------------------------------
    if ($Mode -eq "DryRun") {
        Write-Log ""
        Write-Log "Mode DryRun -- form TIDAK dikirim."
        Write-Log "Payload:"
        Write-Log $BodyString
        Write-Log ""
        Write-Log "Status: SUCCESS (DryRun)"

        $RunRecord = @{
            runId       = $RunId
            mode        = "dryrun-ps1"
            startedAt   = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
            status      = "success"
            responseUrl = $ResponseUrl
            logFile     = $script:LogFile
        }
        # Merge dengan run record dari FastAPI (jaga sessionId, sessionLabel, dll.)
        $DryRunFilePath = Join-Path $RunsDir "$RunId.json"
        if (Test-Path $DryRunFilePath) {
            try {
                $existing = Get-Content $DryRunFilePath -Raw -Encoding UTF8 | ConvertFrom-Json
                foreach ($prop in $existing.PSObject.Properties) {
                    if (-not $RunRecord.ContainsKey($prop.Name)) {
                        $RunRecord[$prop.Name] = $prop.Value
                    }
                }
            } catch {}
        }
        [System.IO.File]::WriteAllText((Join-Path $RunsDir "$RunId.json"), ($RunRecord | ConvertTo-Json -Depth 5), [System.Text.Encoding]::UTF8)

        $script:ExitCode = 0
        return
    }

    # -------------------------------------------------------------------------
    # Submit mode
    # -------------------------------------------------------------------------
    Write-Log "Mode Submit -- mempersiapkan pengiriman terjadwal..."

    # Check lock
    if (Test-Path $LockFile) {
        $existing = Get-Content $LockFile -Raw
        throw "Scheduler sudah aktif (lock: $existing). Batalkan dulu."
    }

    # Write lock
    [System.IO.File]::WriteAllText($LockFile, $RunId, [System.Text.Encoding]::UTF8)
    Write-Log "Lock dibuat: $LockFile"

    # Prevent sleep
    $SleepCode = @'
using System;
using System.Runtime.InteropServices;
public class SleepPreventer {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
    public const uint ES_CONTINUOUS       = 0x80000000;
    public const uint ES_SYSTEM_REQUIRED  = 0x00000001;
    public const uint ES_DISPLAY_REQUIRED = 0x00000002;
    public static void Prevent() {
        SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
    }
    public static void Allow() {
        SetThreadExecutionState(ES_CONTINUOUS);
    }
}
'@

    Add-Type -TypeDefinition $SleepCode
    [SleepPreventer]::Prevent()
    Write-Log "Sleep prevention aktif."

    # Scheduled attempt times - override > config > default
    $TargetTimes = @("12:59:58", "12:59:59", "13:00:00")
    if ($AttemptTimesOverride -ne "") {
        $TargetTimes = @($AttemptTimesOverride -split ",")
    } elseif ($Config.attemptTimes -and $Config.attemptTimes.Count -gt 0) {
        $TargetTimes = @($Config.attemptTimes)
    }
    $Today        = (Get-Date).ToString("yyyy-MM-dd")
    $AttemptTimes = $TargetTimes | ForEach-Object { [datetime]"$Today $_" }

    Write-Log "Jadwal pengiriman:"
    $AttemptTimes | ForEach-Object { Write-Log "  $_" }

    $RunRecord = @{
        runId        = $RunId
        mode         = "submit"
        startedAt    = (Get-Date -Format "o")
        status       = "scheduled"
        responseUrl  = $ResponseUrl
        logFile      = $script:LogFile
        attemptTimes = $TargetTimes
        results      = @()
    }

    # Merge dengan run record dari FastAPI (jaga sessionId, sessionLabel, dll.)
    $RunFilePath = Join-Path $RunsDir "$RunId.json"
    if (Test-Path $RunFilePath) {
        try {
            $existing = Get-Content $RunFilePath -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($prop in $existing.PSObject.Properties) {
                if (-not $RunRecord.ContainsKey($prop.Name)) {
                    $RunRecord[$prop.Name] = $prop.Value
                }
            }
        } catch {}
    }

    [System.IO.File]::WriteAllText($RunFilePath, ($RunRecord | ConvertTo-Json -Depth 5), [System.Text.Encoding]::UTF8)

    # Send attempts
    $Headers = @{
        "Content-Type" = "application/x-www-form-urlencoded"
        "Referer"      = $ResponseUrl
    }

    $Results       = [System.Collections.Generic.List[object]]::new()
    $OverallStatus = "success"

    foreach ($AttemptTime in $AttemptTimes) {
        $Now  = Get-Date
        $Wait = ($AttemptTime - $Now).TotalSeconds
        if ($Wait -gt 0) {
            Write-Log "Menunggu $([math]::Round($Wait,1)) detik hingga $AttemptTime ..."
            Start-Sleep -Milliseconds ([int]($Wait * 1000))
        }

        Write-Log "Mengirim attempt ke $AttemptTime ..."
        try {
            $Response = Invoke-WebRequest `
                -Uri $ResponseUrl `
                -Method POST `
                -Body $BodyString `
                -Headers $Headers `
                -UseBasicParsing `
                -TimeoutSec 10

            $StatusCode = $Response.StatusCode
            Write-Log "  HTTP $StatusCode"
            $Results.Add(@{ time = $AttemptTime.ToString("o"); status = $StatusCode; error = $null })

            if ($StatusCode -ne 200) { $OverallStatus = "partial" }
        }
        catch {
            $ErrMsg = $_.Exception.Message
            # Google Forms sering menutup koneksi setelah menerima data - ini normal
            $isConnectionClosed = $ErrMsg -match "connection was closed|connection forcibly closed|underlying connection|The request was aborted"
            if ($isConnectionClosed) {
                Write-Log "  OK (koneksi ditutup server - form kemungkinan terkirim)"
                $Results.Add(@{ time = $AttemptTime.ToString("o"); status = "ok-closed"; error = $null })
            } else {
                Write-Log "  ERROR: $ErrMsg"
                $Results.Add(@{ time = $AttemptTime.ToString("o"); status = $null; error = $ErrMsg })
                $OverallStatus = "partial"
            }
        }
    }

    # Cleanup
    [SleepPreventer]::Allow()
    Write-Log "Sleep prevention dimatikan."

    if (Test-Path $LockFile) {
        Remove-Item $LockFile -Force
        Write-Log "Lock dihapus."
    }

    Write-Log "Status akhir: $OverallStatus"
    Write-Log "============================================"

    $RunRecord.status  = $OverallStatus
    $RunRecord.results = $Results
    $RunRecord.endedAt = (Get-Date -Format "o")

    # Merge final (jaga sessionId dll.)
    if (Test-Path $RunFilePath) {
        try {
            $existing = Get-Content $RunFilePath -Raw -Encoding UTF8 | ConvertFrom-Json
            foreach ($prop in $existing.PSObject.Properties) {
                if (-not $RunRecord.ContainsKey($prop.Name)) {
                    $RunRecord[$prop.Name] = $prop.Value
                }
            }
        } catch {}
    }

    [System.IO.File]::WriteAllText($RunFilePath, ($RunRecord | ConvertTo-Json -Depth 5), [System.Text.Encoding]::UTF8)

    if ($OverallStatus -eq "success") { $script:ExitCode = 0 } else { $script:ExitCode = 1 }

} catch {
    $ErrMsg = $_.Exception.Message
    Write-Host ""
    Write-Host "=== ERROR ===" -ForegroundColor Red
    Write-Host $ErrMsg -ForegroundColor Red
    if ($script:LogFile) {
        Write-Log "FATAL ERROR: $ErrMsg"
    }
    $script:ExitCode = 1
} finally {
    Write-Host ""
    Write-Host "Terminal akan ditutup dalam 30 detik..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

exit $script:ExitCode
