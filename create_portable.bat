@echo off
REM Create a portable TrustLens Backend package
REM This creates a folder with Python + dependencies that users can run

echo ============================================
echo TrustLens Backend - Portable Package Creator
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [Step 1/5] Creating portable directory...
mkdir portable-trustlens 2>nul
cd portable-trustlens

echo [Step 2/5] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [Step 3/5] Installing dependencies...
pip install -r ..\requirements.txt
pip install -r ..\api\toxicity_model\requirements.txt

echo [Step 4/5] Copying application files...
xcopy /E /I /Y ..\api api
copy ..\launcher.py .
copy ..\run_server.bat start-server.bat

echo [Step 5/5] Creating startup script...
(
echo @echo off
echo echo Starting TrustLens Backend...
echo call venv\Scripts\activate.bat
echo python launcher.py
echo pause
) > start-server.bat

cd ..

echo.
echo ============================================
echo Portable package created successfully!
echo ============================================
echo.
echo Location: portable-trustlens\
echo.
echo To use:
echo   1. Copy the 'portable-trustlens' folder to any location
echo   2. Double-click 'start-server.bat' inside the folder
echo.
echo Note: First run will download ML models (may take time)
echo.
pause
