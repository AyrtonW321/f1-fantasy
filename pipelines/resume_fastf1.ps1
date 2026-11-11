$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$userTemp = Join-Path $env:USERPROFILE "AppData\Local\Temp"
$env:UV_PROJECT_ENVIRONMENT = Join-Path $userTemp "f1-fantasy-uv-env"
$env:FASTF1_CACHE_DIR = Join-Path $userTemp "f1-fastf1-cache"
$runLog = Join-Path $userTemp "f1-fastf1-resume.log"
$summaryPath = Join-Path $repoRoot "reports\fastf1_ingest_summary.md"

function Write-RunLog([string] $message) {
    "$(Get-Date -Format o) $message" | Add-Content -LiteralPath $runLog -Encoding UTF8
}

# Limit detailed FastF1 data to 2025-2026 as requested. Let the active 500-calls/hour window expire first.
Write-RunLog "Waiting one hour before resuming the 2025-2026 cached archive pull."
Start-Sleep -Seconds 3600

while ($true) {
    Write-RunLog "Starting FastF1 resume pass."
    & uv run --offline python -m src.ingest.fastf1_pull --season 2025 --season 2026 2>&1 |
        Tee-Object -FilePath $runLog -Append
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-RunLog "2025-2026 FastF1 archive pull completed with no missing sessions."
        break
    }

    $summary = if (Test-Path -LiteralPath $summaryPath) {
        Get-Content -LiteralPath $summaryPath -Raw
    } else {
        ""
    }
    if ($summary -notmatch "RateLimitExceededError") {
        Write-RunLog "FastF1 resume stopped with exit code $exitCode and no rate-limit marker; review the ingest summary."
        exit $exitCode
    }

    Write-RunLog "FastF1 rate limit reached; cached results are saved. Waiting one hour before the next pass."
    Start-Sleep -Seconds 3600
}
