# TrustLens - Packaging Instructions

## Files and Folders to Include in the Zip

When creating a zip file to distribute to customers, ensure you include the following:

### Required Files
- `START_TRUSTLENS.bat` - One-click startup script
- `launcher.py` - Application launcher
- `requirements.txt` - Python dependencies
- `README.md` - User documentation

### Required Directories
- `api/` - Backend API code (entire folder with all Python files)
- `chrome-extension/` - Browser extension files
- `artifacts/` - **IMPORTANT: Include this folder with .gitkeep file**
- `api/performance_logs/` - **IMPORTANT: Include this folder with .gitkeep file**

### What NOT to Include
- `__pycache__/` folders
- `.pyc` files
- `.git/` folder
- `nul` file
- Test files (`test_*.py`)
- Development files

## How to Create the Distribution Zip

1. Delete all `__pycache__` folders and `.pyc` files
2. Delete the `nul` file if it exists
3. Delete test files (test_*.py)
4. Keep the `artifacts/` and `api/performance_logs/` folders (they contain .gitkeep files)
5. Zip the entire TrustLens folder

## What Happens on Customer Side

When customers run `START_TRUSTLENS.bat`:
1. ✅ Python installation is checked
2. ✅ pip installation is verified
3. ✅ `artifacts/` and `api/performance_logs/` directories are created (if missing)
4. ✅ Dependencies are installed from `requirements.txt`
5. ✅ The TrustLens backend server starts

## Troubleshooting

If artifacts are not being created on customer machines:
- Ensure the `artifacts/` folder exists in the zip (with .gitkeep file)
- Check that customers have write permissions in the folder
- Verify Python is installed correctly
- Check that all dependencies installed successfully
