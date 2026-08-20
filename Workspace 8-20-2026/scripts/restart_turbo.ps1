# restart_turbo.ps1 — preserve data, wipe OLD cartesian cache, launch v20.
#   .\scripts\restart_turbo.ps1
# Ctrl+C any old run first.

param(
    [string]$Seeds = "1,2,3",
    [string]$Opps = "all",
    [int]$Finalists = 20,
    [int]$Procs = 8,
    [switch]$BuildAgent
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== restart_turbo v20 ===" -ForegroundColor Cyan

$ledger = "data\supersearch\ledger_turbo.jsonl"
if (Test-Path $ledger) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $dst = "data\supersearch\ledger_turbo_$stamp.jsonl"
    Copy-Item $ledger $dst
    Write-Host "Preserved old ledger -> $dst" -ForegroundColor Green
} else {
    Write-Host "No old ledger found." -ForegroundColor Yellow
}

foreach ($c in @("data\supersearch\cache", "data\supersearch\cache_records")) {
    if (Test-Path $c) {
        Remove-Item -Recurse -Force $c
        Write-Host "Removed old cache: $c" -ForegroundColor Green
    }
}

$cmd = @(
    "scripts\supersearch_turbo.py",
    "--seeds", $Seeds,
    "--opps", $Opps,
    "--finalists", "$Finalists",
    "--procs", "$Procs",
    "--mode", "surgical",
    "--fresh"
)
if ($BuildAgent) { $cmd += "--build-agent" }

Write-Host "Launching: python $cmd" -ForegroundColor Cyan
python @cmd
