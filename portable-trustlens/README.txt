========================================
TrustLens Backend - Portable Package
========================================

This is a portable, self-contained version of the TrustLens Backend.
You can copy this entire folder anywhere and run it without installing Python!

HOW TO USE:
-----------

1. FIRST TIME SETUP:
   - Double-click "START_SERVER.bat"
   - The first run will automatically install all dependencies
   - This takes 5-10 minutes (downloads ML models)
   - Wait for it to complete

2. SUBSEQUENT RUNS:
   - Just double-click "START_SERVER.bat"
   - Server starts immediately (no installation needed)

3. SERVER INFO:
   - Server runs at: http://127.0.0.1:8000
   - Health check: http://127.0.0.1:8000/health
   - Press CTRL+C in the console window to stop

WHAT'S INCLUDED:
----------------
- Python virtual environment (venv/)
- TrustLens Backend code (api/)
- Launcher script (launcher.py)
- All dependencies (auto-installed on first run)

FOLDER STRUCTURE:
-----------------
portable-trustlens/
├── START_SERVER.bat    <-- Double-click this to run!
├── README.txt          <-- You are here
├── venv/              <-- Python environment
├── api/               <-- Backend code
├── launcher.py        <-- Server launcher
├── requirements.txt   <-- Dependencies
├── artifacts/         <-- Created when server runs
└── api/performance_logs/  <-- Created when server runs

TROUBLESHOOTING:
----------------

Problem: "Python is not recognized"
Solution: You need Python 3.8+ installed. Download from python.org

Problem: Server won't start
Solution: Check if port 8000 is already in use. Close other applications.

Problem: ML model errors
Solution: Delete venv/ folder and run START_SERVER.bat again

DISTRIBUTION:
-------------
To share this with others:
1. Zip the entire "portable-trustlens" folder
2. Send the zip file
3. Recipients extract and run START_SERVER.bat

Note: Recipients still need Python installed on their system.
For a truly standalone version, they would need to install Python first.

========================================
