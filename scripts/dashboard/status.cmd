@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
if not exist "%ROOT%\.venv\Scripts\qseh.exe" (
  echo [qseh] Missing .venv\Scripts\qseh.exe
  exit /b 1
)
"%ROOT%\.venv\Scripts\qseh.exe" dashboard status
exit /b %ERRORLEVEL%
