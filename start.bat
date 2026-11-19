@echo off
setlocal enabledelayedexpansion

title APH Hospital Intranet Server (Python Engine)
cd /d "%~dp0"

set PORT=1111
if not "%~1"=="" set PORT=%~1

echo ========================================================================
echo 🏥 Starting APH Hospital Intranet Server on Port: %PORT%
echo ========================================================================

:: 1. Check if Python is installed
set PY_CMD=
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PY_CMD=python
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 (
        set PY_CMD=py
    )
)

if "%PY_CMD%"=="" (
    echo.
    echo ❌ Error: Python is NOT installed or not added to Windows PATH.
    echo.
    echo Please download and install Python (3.9+) from:
    echo 👉 https://www.python.org/downloads/
    echo.
    echo ⚠️ IMPORTANT: When installing Python, make sure to check:
    echo    "[x] Add python.exe to PATH"
    echo.
    echo After installing Python, run start.bat again.
    echo ========================================================================
    pause
    exit /b 1
)

:: 2. Check if required files exist in current folder
if not exist "server.py" (
    echo.
    echo ❌ Error: server.py was not found in this folder!
    echo Current Directory: %cd%
    echo Please make sure you are running start.bat inside the project folder.
    echo ========================================================================
    pause
    exit /b 1
)

:: 3. Terminate any previous process listening on this port
for %%p in (%PORT% 1234 3000 2222) do (
    for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo ⚠️  Found previous process running on port %%p (PID: %%a). Stopping...
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo.
echo ========================================================================
echo 🚀 APH Hospital Portal Starting (Port %PORT%)...
echo.
echo 🌐 Access URLs:
echo    • Localhost:       http://localhost:%PORT%
echo    • Hospital LAN:    http://192.168.101.75:%PORT%
echo.
echo ℹ️  Keep this Command Prompt window open while using the portal.
echo    To stop the server: Press Ctrl + C or run stop.bat.
echo ========================================================================
echo.

%PY_CMD% server.py %PORT%

if %errorlevel% neq 0 (
    echo.
    echo ❌ Server stopped with error code %errorlevel%.
    pause
)
