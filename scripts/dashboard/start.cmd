@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist "%ROOT%\.venv\Scripts\qseh.exe" (
  echo [qseh] Missing .venv\Scripts\qseh.exe — create venv and pip install -e ".[dashboard,dev]" first.
  exit /b 1
)
"%ROOT%\.venv\Scripts\qseh.exe" dashboard start
exit /b %ERRORLEVEL%
