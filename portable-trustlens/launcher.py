"""
TrustLens Backend Launcher
This script starts the FastAPI backend server when the executable is run.
"""
import sys
import os
import uvicorn
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_base_path():
    """Get the base path whether running from source or frozen executable."""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys._MEIPASS)
    else:
        # Running as script
        return Path(__file__).parent

def setup_paths():
    """Setup necessary paths for the application."""
    base_path = get_base_path()

    # Change working directory to the executable location
    # This ensures artifacts and logs are created in the right place
    if getattr(sys, 'frozen', False):
        # Running as executable - change to exe directory
        exe_dir = Path(sys.executable).parent
        os.chdir(exe_dir)
        logger.info(f"Changed working directory to: {exe_dir}")

    # Add api directory to Python path
    api_path = base_path / 'api'
    if str(api_path) not in sys.path:
        sys.path.insert(0, str(api_path))

    # Ensure artifacts and performance_logs directories exist
    artifacts_dir = Path('artifacts')
    artifacts_dir.mkdir(exist_ok=True)

    perf_logs_dir = Path('api/performance_logs')
    perf_logs_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Base path: {base_path}")
    logger.info(f"Working directory: {Path.cwd()}")
    logger.info(f"API path: {api_path}")
    logger.info(f"Artifacts directory: {artifacts_dir.absolute()}")
    logger.info(f"Performance logs directory: {perf_logs_dir.absolute()}")

def start_server():
    """Start the FastAPI server."""
    try:
        print("=" * 60)
        print("TrustLens Backend Server")
        print("=" * 60)
        print("Initializing...")
        print()

        setup_paths()

        logger.info("=" * 60)
        logger.info("TrustLens Backend Server Starting...")
        logger.info("=" * 60)
        logger.info("Server will be available at: http://127.0.0.1:8000")
        logger.info("Health check endpoint: http://127.0.0.1:8000/health")
        logger.info("Press CTRL+C to stop the server")
        logger.info("=" * 60)

        print("\nImporting application modules...")
        # Import the FastAPI app
        from api.main import app
        print("Modules loaded successfully!")
        print()

        # Start uvicorn server
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info"
        )

    except KeyboardInterrupt:
        print("\n")
        logger.info("Server stopped by user")
        print("\nPress Enter to exit...")
        input()
    except ImportError as e:
        print("\n" + "=" * 60)
        print("ERROR: Failed to import required modules")
        print("=" * 60)
        print(f"\nDetails: {e}")
        print("\nThis usually means:")
        print("1. The executable wasn't built correctly")
        print("2. Some dependencies are missing")
        print("3. Try rebuilding with: build.bat")
        print("\nFull error:")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print("ERROR: Server failed to start")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("Press Enter to exit...")
        input()
        sys.exit(1)

if __name__ == "__main__":
    try:
        start_server()
    except Exception as e:
        print("\n" + "=" * 60)
        print("CRITICAL ERROR")
        print("=" * 60)
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)
