@echo off
REM ============================================================
REM AI Employee Vault - Unified Start
REM ============================================================

echo.
echo ============================================================
echo   AI Employee Vault - Starting...
echo ============================================================
echo.
echo [1/3] Checking Docker and starting Odoo...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 goto START_DOCKER

:DOCKER_READY
echo Starting Odoo containers...
docker compose up -d --quiet-pull
if %errorlevel% equ 0 (
    echo [OK] Odoo started at: http://localhost:8069
) else (
    echo [WARNING] Failed to start Odoo containers
)
echo.

echo [2/3] Starting Dashboard...
echo.
start "AI Employee Vault Dashboard" python dashboard_server.py

echo [3/3] Dashboard started at: http://localhost:3000
echo.
echo ============================================================
echo Done! Open http://localhost:3000 in your browser
echo ============================================================
echo.
pause
goto END

:START_DOCKER
echo [INFO] Docker Desktop is not running. Starting it now...
echo.
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Waiting for Docker to start (up to 60 seconds)...
echo.

set /a timeout=0
:WAIT_LOOP
timeout /t 5 /nobreak >nul
docker info >nul 2>&1
if %errorlevel% equ 0 goto DOCKER_STARTED
set /a timeout+=5
if %timeout% LSS 60 goto WAIT_LOOP

echo [WARNING] Docker did not start in time
echo Press any key to continue without Odoo, or Ctrl+C to cancel
pause >nul
goto DOCKER_READY

:DOCKER_STARTED
echo [OK] Docker is now running!
echo.
goto DOCKER_READY

:END
