@echo off
REM TrustLens Backend - Portable Launcher
echo ============================================
echo TrustLens Backend Server
echo ============================================
echo.

REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run create_portable.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Check if this is first run
if not exist "venv\Lib\site-packages\fastapi" (
    echo First-time setup detected...
    echo Installing dependencies (this will take a few minutes)...
    echo.
    call venv\Scripts\activate.bat
    if errorlevel 1 (
        echo ERROR: Failed to activate virtual environment
        pause
        exit /b 1
    )

    echo Installing main requirements...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install main requirements
        pause
        exit /b 1
    )

    echo Installing toxicity model requirements...
    pip install -r api\toxicity_model\requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install toxicity model requirements
        pause
        exit /b 1
    )

    echo.
    echo Installation complete!
    echo.
)

echo Starting server...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

python launcher.py
if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start
    echo Check the error messages above
)

echo.
pause
