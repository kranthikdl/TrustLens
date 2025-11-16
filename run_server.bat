@echo off
REM TrustLens Backend Server Launcher
REM This batch file ensures the executable runs with the correct working directory

cd /d "%~dp0"
trustlens-backend.exe
pause
