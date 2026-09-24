# turbo.ps1 — run the v20 SURGICAL supersearch.
#
#   cd Z:\Kaggle\Works\kaggriculture
#   .\scripts\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -Procs 8 -BuildAgent
#
# First run after downloading this folder, wipe the old cartesian cache:
#   Remove-Item -Recurse -Force data\supersearch\cache, data\supersearch\cache_records -ErrorAction SilentlyContinue; .\scripts\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -Procs 8 -BuildAgent
#
# Resume after a reboot: run the same command. Ledger is kept. Use -Fresh to start over (ledger is backed up first).

param(
    [string]$Seeds = "1,2,3",
    [string]$GateSeeds = "1",
    [string]$Opps = "all",
    [string]$Dims = "",
    [string]$Mode = "surgical",
    [int]$Procs = 8,
    [int]$Finalists = 20,
    [int]$Threshold = 200,
    [switch]$BuildAgent,
    [switch]$Fresh
)

$cmd = @(
    "scripts\supersearch_turbo.py",
    "--seeds", $Seeds,
    "--gate-seeds", $GateSeeds,
    "--opps", $Opps,
    "--mode", $Mode,
    "--finalists", "$Finalists",
    "--threshold", "$Threshold",
    "--procs", "$Procs"
)
if ($Dims)      { $cmd += "--dims"; $cmd += $Dims }
if ($BuildAgent) { $cmd += "--build-agent" }
if ($Fresh)      { $cmd += "--fresh" }

Write-Host "Running: python $cmd"
python @cmd
