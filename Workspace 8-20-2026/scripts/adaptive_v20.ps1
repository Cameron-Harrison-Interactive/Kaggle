# adaptive_v20.ps1 — run the v20 adaptive battery.
#
#   cd Z:\Kaggle\Works\kaggriculture
#   powershell -ExecutionPolicy Bypass -File scripts\adaptive_v20.ps1 -Seeds "1,2,3" -Procs 8 -Finals -BuildAgent
#
# If PowerShell blocks the script ("not digitally signed"), use one of:
#   1) powershell -ExecutionPolicy Bypass -File scripts\adaptive_v20.ps1 ...
#   2) scripts\run_adaptive_v20.bat (no policy involved)
#   3) the plain python line (always works):
#        python scripts\adaptive_v20.py --seeds 1,2,3 --procs 8 --finals --build-agent

param(
    [string]$Seeds = "1,2,3",
    [int]$Procs = 8,
    [switch]$Quick,
    [switch]$WithMelon4,
    [switch]$Finals,
    [switch]$BuildAgent,
    [string]$Version = "HI_AgriBot_v20_Adaptive",
    [switch]$SelfTest
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$cmd = @(
    "scripts\adaptive_v20.py",
    "--seeds", $Seeds,
    "--procs", "$Procs"
)
if ($Quick)      { $cmd += "--quick" }
if ($WithMelon4) { $cmd += "--with-melon4" }
if ($Finals)     { $cmd += "--finals" }
if ($BuildAgent) { $cmd += "--build-agent"; $cmd += "--version"; $cmd += $Version }
if ($SelfTest)   { $cmd += "--self-test" }

Write-Host "Running: python $cmd" -ForegroundColor Cyan
python @cmd
