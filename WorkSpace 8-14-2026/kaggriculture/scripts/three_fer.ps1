# three_fer.ps1 — leftover walker + tetsu/seat1 counter + distinctive path.
#
#   cd Z:\Kaggle\Works\kaggriculture
#   .\scripts\three_fer.ps1 -Seeds "1,2,3" -Procs 8
#   .\scripts\three_fer.ps1 -DiagnoseOnly
#   .\scripts\three_fer.ps1 -Quick -Procs 8
#   .\scripts\three_fer.ps1 -Seeds "1,2,3" -Procs 8 -BuildAgent
#
# NOT a cartesian. ~20 local one-offs. Minutes on a 3700X.
# Do NOT ship unless the report says SHIP=YES. Keep HI_AgriBot_v18 live.

param(
    [string]$Seeds = "1,2,3",
    [string]$GateSeeds = "1,2,3",
    [int]$Procs = 8,
    [switch]$DiagnoseOnly,
    [switch]$Quick,
    [switch]$BuildAgent
)

$cmd = @(
    "scripts\three_fer.py",
    "--seeds", $Seeds,
    "--gate-seeds", $GateSeeds,
    "--procs", "$Procs"
)
if ($DiagnoseOnly) { $cmd += "--diagnose-only" }
if ($Quick)        { $cmd += "--quick" }
if ($BuildAgent)   { $cmd += "--build-agent" }

Write-Host "Running: python $cmd"
python @cmd
