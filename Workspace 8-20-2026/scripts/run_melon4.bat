@echo off
REM run_melon4.bat — the melon4 compiler search. NO TYPING NEEDED.
REM
REM   cd Z:\Kaggle\Works\kaggriculture
REM   scripts\run_melon4.bat
REM
REM Runs: adaptive_v20.py --with-melon4 --procs 8 --finals --build-agent
REM (the rayk +4-melon economy edge search; see data\adaptive_v20\README.md)

cd /d "%~dp0.."
python scripts\adaptive_v20.py --with-melon4 --procs 8 --finals --build-agent
pause
