@echo off
REM run_adaptive_v20.bat — the v20 adaptive battery (no PowerShell policy issues).
REM
REM   cd Z:\Kaggle\Works\kaggriculture
REM   scripts\run_adaptive_v20.bat
REM
REM Options (edit the line below):
REM   --quick             3 variants only (v19ctrl, s0s1, s0s1+race)
REM   --with-melon4       add the compiled melon4 variants (slow: compiles both seats)
REM   --finals            full 9-opponent battery on the top candidates
REM   --build-agent       write agent\main_v20_adaptive.py if something ships
REM   --seeds 1,2,3       contested seeds

cd /d "%~dp0.."
python scripts\adaptive_v20.py --seeds 1,2,3 --procs 8 --finals --build-agent
pause
