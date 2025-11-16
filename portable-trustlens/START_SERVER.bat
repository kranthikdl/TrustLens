@echo off
REM TrustLens Backend - Portable Launcher
echo ============================================
echo TrustLens Backend Server
echo ============================================
echo.

REM Check if this is first run
if not exist "venv\Lib\site-packages\fastapi" (
    echo First-time setup detected...
    echo Installing dependencies (this will take a few minutes)...
    echo.
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    pip install -r api\toxicity_model\requirements.txt
    echo.
    echo Installation complete!
    echo.
)

echo Starting server...
call venv\Scripts\activate.bat
python launcher.py

pause
