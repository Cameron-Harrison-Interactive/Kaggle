# restart_turbo.ps1 — stop old run, preserve its data, wipe old cache, launch the NEW turbo.
# Run this in the kaggriculture folder:
#   .\scripts\restart_turbo.ps1
# (First Ctrl+C the old run in its own terminal, or just run this — it will start
#  fresh while the old one may still be finishing; better to Ctrl+C it first.)

param(
    [string]$Seeds = "1,2,3",
    [string]$Opps = "all",
    [int]$Finalists = 20,
    [switch]$BuildAgent
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "=== restart_turbo ===" -ForegroundColor Cyan

# 1) preserve the old ledger if it exists
$ledger = "data\supersearch\ledger_turbo.jsonl"
if (Test-Path $ledger) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $dst = "data\supersearch\ledger_turbo_$stamp.jsonl"
    Copy-Item $ledger $dst
    Write-Host "Preserved old ledger -> $dst" -ForegroundColor Green
} else {
    Write-Host "No old ledger found, nothing to preserve." -ForegroundColor Yellow
}

# 2) wipe OLD caches (written by the pre-cache engine — must go for the new one)
foreach ($c in @("data\supersearch\cache", "data\supersearch\cache_records")) {
    if (Test-Path $c) {
        Remove-Item -Recurse -Force $c
        Write-Host "Removed old cache: $c" -ForegroundColor Green
    }
}

# 3) launch the NEW turbo run
$cmd = @(
    "scripts\supersearch_turbo.py",
    "--seeds", $Seeds,
    "--opps", $Opps,
    "--finalists", "$Finalists"
)
if ($BuildAgent) { $cmd += "--build-agent" }

Write-Host "Launching: python $cmd" -ForegroundColor Cyan
python @cmd
