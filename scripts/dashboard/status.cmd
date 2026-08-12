@echo off
setlocal EnableExtensions
set "ROOT=%~dp0..\.."
set "PIDFILE=%ROOT%\runs\state\dashboard.pid"
set "PORT=8766"

echo [qseh] Dashboard status
if exist "%PIDFILE%" (
  set /p PID=<"%PIDFILE%"
  echo pidfile=%PID%
) else (
  echo pidfile=MISSING
)

netstat -ano | findstr ":%PORT% " | findstr LISTENING
if errorlevel 1 (
  echo listening=NO
  exit /b 1
)

"%ROOT%\.venv\Scripts\python.exe" -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8766/api/health', timeout=3).read().decode())"
endlocal
exit /b 0
