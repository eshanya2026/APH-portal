@echo off
setlocal enabledelayedexpansion

title Stop APH Hospital Intranet Server
cd /d "%~dp0"

set PORT=3000
if not "%~1"=="" set PORT=%~1

echo ========================================================================
echo 🛑 Stopping APH Hospital Intranet Server on Port: %PORT%
echo ========================================================================

set STOPPED=0

:: Terminate any process listening on the port
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    echo Terminating process on port %PORT% (PID: %%a)...
    taskkill /F /PID %%a >nul 2>&1
    set STOPPED=1
)

:: Terminate any lingering server.py processes
wmic process where "commandline like '%%server.py%%'" call terminate >nul 2>&1

:: Also terminate any lingering node processes
wmic process where "commandline like '%%node%%server.js%%'" call terminate >nul 2>&1

if %STOPPED% equ 1 (
    echo ✅ Server on port %PORT% successfully stopped.
) else (
    echo ℹ️  No active server found listening on port %PORT%.
)

echo ========================================================================
timeout /t 3 >nul
