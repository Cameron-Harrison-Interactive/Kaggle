@echo off
REM run_three_fer.bat — the v20-based three-fer (no PowerShell policy issues).
REM
REM   cd Z:\Kaggle\Works\kaggriculture
REM   scripts\run_three_fer.bat
REM
REM Quick (4 candidates: BASE, px, esp, px+esp):   scripts\run_three_fer.bat quick
REM Full (48 candidates):                          scripts\run_three_fer.bat full
REM Diagnose only:                                 scripts\run_three_fer.bat diag

cd /d "%~dp0.."
if "%1"=="quick" goto quick
if "%1"=="diag" goto diag
python scripts\three_fer.py --seeds 1,2,3 --gate-seeds 1,2,3 --procs 8 --build-agent
goto end
:quick
python scripts\three_fer.py --quick --procs 8
goto end
:diag
python scripts\three_fer.py --diagnose-only
goto end
:end
pause
