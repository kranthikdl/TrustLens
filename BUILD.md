# Building TrustLens Backend Executable

This guide explains how to build a standalone `trustlens-backend.exe` that includes all dependencies and can be run with a single click.

## Prerequisites

- Python 3.8 or higher installed
- Git (to clone the repository)
- Windows OS (for .exe build)

## Quick Build (Recommended)

Simply double-click `build.bat` or run it from command prompt:

```batch
build.bat
```

This script will:
1. Install PyInstaller
2. Install all project dependencies
3. Clean previous build artifacts
4. Build the standalone executable

## Manual Build Steps

If you prefer to build manually:

### 1. Install Dependencies

```powershell
# Install PyInstaller
pip install pyinstaller

# Install project dependencies
pip install -r requirements.txt
pip install -r api\toxicity_model\requirements.txt
```

### 2. Build the Executable

```powershell
pyinstaller trustlens-backend.spec
```

### 3. Find Your Executable

The executable will be located at:
```
dist\trustlens-backend\trustlens-backend.exe
```

## Running the Executable

### First Time Setup

1. Navigate to `dist\trustlens-backend\`
2. Double-click `trustlens-backend.exe`
3. A console window will open showing:
   ```
   TrustLens Backend Server Starting...
   Server will be available at: http://127.0.0.1:8000
   ```
4. The server is now running!

### Using the Application

Once the server is running:
- Health check: http://127.0.0.1:8000/health
- The server will process Reddit posts from the Chrome extension
- Results are saved in the `artifacts` folder
- Performance logs are saved in `api/performance_logs`

### Stopping the Server

Press `CTRL+C` in the console window or simply close the window.

## Distribution

To distribute the application to others:

1. Compress the entire `dist\trustlens-backend\` folder
2. Share the compressed file
3. Users simply extract and run `trustlens-backend.exe`

**Important**: The entire folder is needed, not just the .exe file, as it contains:
- Python runtime
- ML models (transformers, torch)
- All dependencies
- Application code

## Troubleshooting

### Build Fails

**Issue**: PyInstaller installation fails
- **Solution**: Upgrade pip: `python -m pip install --upgrade pip`

**Issue**: "Module not found" error during build
- **Solution**: Ensure all dependencies are installed: `pip install -r requirements.txt`

**Issue**: Build takes very long time
- **Solution**: This is normal. Building with ML models (torch, transformers) can take 10-20 minutes.

### Runtime Issues

**Issue**: Server fails to start
- **Solution**: Check if port 8000 is already in use. Close other applications using that port.

**Issue**: "artifacts" or "performance_logs" folder errors
- **Solution**: These folders are created automatically. Run the exe from a location where you have write permissions.

**Issue**: ML model loading errors
- **Solution**: Ensure you built the executable with all dependencies installed. The first run may take longer as models are loaded.

### Size Optimization

The executable folder will be large (500MB - 2GB) due to:
- PyTorch ML framework
- Transformers library
- Pre-trained models

This is normal for ML applications. If size is a concern:
- Use PyInstaller with `--onefile` mode (slower startup)
- Consider server deployment instead of standalone executable

## Development Notes

### Files Created for Building

- `launcher.py` - Entry point that starts the FastAPI server
- `trustlens-backend.spec` - PyInstaller configuration
- `build.bat` - Automated build script

### Modifying the Build

To add new dependencies:
1. Add them to `requirements.txt`
2. If needed, add to `hidden_imports` in `trustlens-backend.spec`
3. Rebuild using `build.bat`

To change server settings:
- Edit `launcher.py` to modify host, port, or logging

## Technical Details

### What's Bundled

The executable includes:
- Python interpreter
- FastAPI and Uvicorn
- PyTorch and Transformers (ML models)
- All application code from `api/` directory
- Supporting libraries (httpx, requests, beautifulsoup4, etc.)

### How It Works

1. `launcher.py` is the entry point
2. It sets up paths for bundled and external resources
3. Imports the FastAPI app from `api.main`
4. Starts Uvicorn server on localhost:8000
5. Creates necessary directories (artifacts, performance_logs)

### Extraction Process

When you run the .exe:
1. PyInstaller extracts bundled files to a temporary directory (`_MEIPASS`)
2. Application code runs from this temporary location
3. Output files (artifacts, logs) are saved to current directory

## Next Steps

After building:
1. Test the executable thoroughly
2. Create user documentation
3. Consider creating an installer (using Inno Setup or NSIS)
4. Add an application icon for better UX

## License

Same as TrustLens project (MIT License)
