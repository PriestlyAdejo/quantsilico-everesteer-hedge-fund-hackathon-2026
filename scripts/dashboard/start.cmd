@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo [qseh] Missing .venv — create it and install deps first.
  exit /b 1
)

set "QSEH_DASHBOARD_HOST=127.0.0.1"
set "QSEH_DASHBOARD_PORT=8766"
set "PIDFILE=%ROOT%\runs\state\dashboard.pid"

if not exist "%ROOT%\runs\state" mkdir "%ROOT%\runs\state"

if exist "%ROOT%\dashboard\frontend\dist\index.html" goto :serve
echo [qseh] Frontend dist missing — building...
pushd "%ROOT%\dashboard\frontend"
call pnpm install --frozen-lockfile
if errorlevel 1 (
  echo [qseh] pnpm install failed
  popd
  exit /b 1
)
call pnpm run build
if errorlevel 1 (
  echo [qseh] frontend build failed
  popd
  exit /b 1
)
popd

:serve
echo [qseh] Starting Research Console on http://%QSEH_DASHBOARD_HOST%:%QSEH_DASHBOARD_PORT%
start "qseh-dashboard" /b "%ROOT%\.venv\Scripts\python.exe" -m uvicorn dashboard.backend.app.main:app --host %QSEH_DASHBOARD_HOST% --port %QSEH_DASHBOARD_PORT%
timeout /t 1 /nobreak >nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%QSEH_DASHBOARD_PORT% " ^| findstr LISTENING') do (
  echo %%P>"%PIDFILE%"
  echo [qseh] listening pid=%%P
  goto :done
)
echo [qseh] started (pid file may lag — use status.cmd)
:done
endlocal
exit /b 0
