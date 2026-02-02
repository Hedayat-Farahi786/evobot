@echo off
TITLE EvoBot Dashboard
echo ===================================================
echo       EvoBot - Algo Trading System
echo ===================================================
echo.

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] "venv" not found. Using system Python...
)

echo.
echo [INFO] Starting Dashboard...
echo [INFO] Access at http://localhost:8080
echo.

python start_dashboard.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Bot crashed or stopped with error.
    pause
)
