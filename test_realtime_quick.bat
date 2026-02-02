@echo off
REM Quick test script for real-time sync (Windows)

echo ==================================
echo EvoBot Real-Time Sync Quick Test
echo ==================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo [!] Virtual environment not activated
    echo     Run: venv\Scripts\activate
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
)

echo ==================================
echo Test 1: Automated Test Suite
echo ==================================
echo.
echo Running comprehensive tests...
echo.

python test_realtime_sync.py

if errorlevel 1 (
    echo.
    echo X Some tests failed. Check logs above.
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] All automated tests passed!
echo.

echo ==================================
echo Test 2: Visual Dashboard Test
echo ==================================
echo.
echo Starting dashboard...
echo.
echo Instructions:
echo    1. Dashboard will start on http://localhost:8080
echo    2. Open http://localhost:8080/test-realtime in your browser
echo    3. Click 'Start Bot' from main dashboard
echo    4. Watch real-time updates on test page
echo    5. Press Ctrl+C here to stop
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul

python start_dashboard.py
