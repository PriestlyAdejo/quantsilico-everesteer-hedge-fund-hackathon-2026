@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\.."
set "PIDFILE=%ROOT%\runs\state\dashboard.pid"
set "PORT=8766"

if exist "%PIDFILE%" (
  set /p PID=<"%PIDFILE%"
  if defined PID (
    taskkill /PID %PID% /F >nul 2>&1
    echo [qseh] stopped pid=%PID%
  )
  del "%PIDFILE%" >nul 2>&1
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING') do (
  taskkill /PID %%P /F >nul 2>&1
  echo [qseh] stopped listener pid=%%P
)

endlocal
exit /b 0
