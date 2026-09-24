@echo off
REM run_brain_v21.bat — the runtime FieldBrain battery (no PowerShell policy issues).
REM
REM   cd Z:\Kaggle\Works\kaggriculture
REM   scripts\run_brain_v21.bat

cd /d "%~dp0.."
python scripts\brain_v21.py --seeds 1,2 --procs 8 --build-agent
pause
