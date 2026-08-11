# supersearch.ps1 — run the supersearch compiler on Windows PowerShell.
# No backslash line-continuations needed; call it on ONE line like this:
#
#   cd Z:\Kaggle\Works\kaggriculture
#   .\scripts\supersearch.ps1 -Seeds "1,2,3" -Opps all -Iterations 3 -Validate -BuildAgent
#
# Options:
#   -Seeds      battle seeds (default "1,2")
#   -Opps       v18 | ours | all   (default v18; all = every winner + top proxies)
#   -Iterations search passes over the variant grid (default 1, use 3+ for real runs)
#   -Threshold  min avg $ delta vs EVERY opponent to count as beating it (default 200)
#   -Validate   validate each candidate vs PASS (reward/weeds report)
#   -BuildAgent write agent/main_v19.py from the champion tapes

param(
    [string]$Seats = "0,1",
    [string]$Seeds = "1,2",
    [string]$Opps = "v18",
    [int]$Iterations = 1,
    [int]$Threshold = 200,
    [switch]$Validate,
    [switch]$BuildAgent
)

$cmd = @(
    "scripts\supersearch_compiler.py",
    "--seats", $Seats,
    "--seeds", $Seeds,
    "--opps", $Opps,
    "--iterations", "$Iterations",
    "--threshold", "$Threshold"
)
if ($Validate)   { $cmd += "--validate" }
if ($BuildAgent) { $cmd += "--build-agent" }

Write-Host "Running: python $cmd"
python @cmd
