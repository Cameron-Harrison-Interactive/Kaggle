# turbo.ps1 — run the TURBO supersearch (thousands of variants/hour).
#
#   cd Z:\Kaggle\Works\kaggriculture
#   .\scripts\turbo.ps1 -Seeds "1,2,3" -Opps all -Finalists 20 -BuildAgent
#
# Options:
#   -Seeds      finalist battle seeds        (default "1,2")
#   -GateSeeds  fast-gate seeds              (default "1")
#   -Opps       v18 | ours | all             (default ours)
#   -Dims       crop,hires,animals,sell,water,fill,early   (default all)
#   -Procs      worker processes             (default = all cores)
#   -Finalists  top-K gate scores to full-battle (default 20)
#   -Threshold  min avg $ vs EVERY opponent to accept (default 200)
#   -BuildAgent write agent/main_v19.py from the champion

param(
    [string]$Seeds = "1,2",
    [string]$GateSeeds = "1",
    [string]$Opps = "ours",
    [string]$Dims = "",
    [int]$Procs = 0,
    [int]$Finalists = 20,
    [int]$Threshold = 200,
    [switch]$BuildAgent
)

$cmd = @(
    "scripts\supersearch_turbo.py",
    "--seeds", $Seeds,
    "--gate-seeds", $GateSeeds,
    "--opps", $Opps,
    "--finalists", "$Finalists",
    "--threshold", "$Threshold",
    "--procs", "$Procs"
)
if ($Dims)     { $cmd += "--dims"; $cmd += $Dims }
if ($BuildAgent) { $cmd += "--build-agent" }

Write-Host "Running: python $cmd"
python @cmd
