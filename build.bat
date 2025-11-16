@echo off
REM TrustLens Backend Build Script
REM This script builds the standalone executable for TrustLens Backend

echo ============================================
echo TrustLens Backend - Build Script
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [Step 1/4] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller
    pause
    exit /b 1
)

echo.
echo [Step 2/4] Installing project dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

pip install -r api\toxicity_model\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install toxicity model dependencies
    pause
    exit /b 1
)

echo.
echo [Step 3/4] Cleaning previous build artifacts...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo.
echo [Step 4/4] Building executable with PyInstaller...
echo This may take several minutes...
pyinstaller trustlens-backend.spec
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo [Creating launcher shortcuts...]

REM Create a convenient launcher batch file in the dist folder
(
echo @echo off
echo cd /d "%%~dp0trustlens-backend"
echo start "" "trustlens-backend.exe"
) > "dist\Start TrustLens Backend.bat"

echo.
echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo The executable can be found in: dist\trustlens-backend\
echo.
echo To start the server, you can either:
echo   1. Double-click: dist\trustlens-backend\trustlens-backend.exe
echo   2. Or use: dist\Start TrustLens Backend.bat
echo.
echo Note: The first run may take longer as ML models are loaded.
echo.
pause
