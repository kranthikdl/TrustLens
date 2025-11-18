@echo off
REM ============================================================
REM TrustLens - One-Click Startup Script
REM ============================================================
REM This script automatically starts the TrustLens backend server
REM ============================================================

REM Change to the directory where this batch file is located
cd /d "%~dp0"

title TrustLens Backend Server

echo.
echo ============================================================
echo             TrustLens - Starting Backend Server
echo ============================================================
echo.

REM Check if Python is installed
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)
echo       Python is installed!
echo.

REM Check if pip is available
echo [2/4] Checking pip installation...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: pip is not available!
    echo.
    echo Please reinstall Python with pip enabled.
    echo.
    pause
    exit /b 1
)
echo       pip is available!
echo.

REM Create necessary directories
echo [3/5] Creating necessary directories...
if not exist "artifacts" mkdir "artifacts"
if not exist "api\performance_logs" mkdir "api\performance_logs"
echo       Directories ready!
echo.

REM Install/Update requirements
echo [4/5] Installing/Updating dependencies...
echo       This may take a moment on first run...
echo.
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo.
    echo Please check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo       Dependencies installed successfully!
echo.

REM Start the backend server
echo [5/5] Starting TrustLens backend server...
echo.
echo ============================================================
echo Server will start at: http://127.0.0.1:8000
echo Press CTRL+C to stop the server
echo ============================================================
echo.

python launcher.py

REM If the server stops, wait for user input
if %errorlevel% neq 0 (
    echo.
    echo Server stopped with an error.
    pause
) else (
    echo.
    echo Server stopped successfully.
    pause
)
