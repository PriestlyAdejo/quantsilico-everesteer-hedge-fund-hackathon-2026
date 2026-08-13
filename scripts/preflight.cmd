@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo [qseh] Missing .venv\Scripts\python.exe - create venv and pip install -e ".[dashboard,dev]" first.
  endlocal
  exit /b 1
)
set "QSEH_SYNTHETIC=1"
".venv\Scripts\python.exe" "scripts\preflight.py"
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
