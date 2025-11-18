# TrustLens - Reddit Toxicity Analyzer

TrustLens is a Chrome extension that analyzes Reddit comments in real-time to detect toxic, harmful, or inappropriate content. It provides visual badges and comprehensive reporting to help you navigate Reddit more safely.

## What's Included

- **Backend Server** (in `api/` folder) - Analyzes comments using advanced toxicity detection
- **Chrome Extension** (in `chrome-extension/` folder) - Displays toxicity badges on Reddit
- **One-Click Startup** - `START_TRUSTLENS.bat` runs everything automatically

## Quick Start Guide

### Prerequisites

You need Python 3.8 or higher installed on your computer.

**Don't have Python?**
1. Download Python from: https://www.python.org/downloads/
2. During installation, **IMPORTANT**: Check the box "Add Python to PATH"
3. Complete the installation

### Step 1: Start the Backend Server

1. Navigate to the TrustLens folder
2. **Double-click** `START_TRUSTLENS.bat`
3. A window will open and automatically:
   - Check your Python installation
   - Install required dependencies
   - Start the backend server
4. Wait until you see: `Server will be available at: http://127.0.0.1:8000`
5. **Keep this window open** while using TrustLens

### Step 2: Install the Chrome Extension

1. Open Google Chrome
2. Go to `chrome://extensions/` in your address bar
3. Enable **Developer mode** (toggle switch in top-right corner)
4. Click **"Load unpacked"** button
5. Navigate to the TrustLens folder and select the `chrome-extension` folder
6. Click **"Select Folder"**
7. The TrustLens extension should now appear in your extensions list

### Step 3: Use TrustLens

1. Make sure the backend server is running (from Step 1)
2. Visit any Reddit post (e.g., https://www.reddit.com/r/AskReddit/)
3. TrustLens will automatically analyze comments and display toxicity badges
4. Click the TrustLens icon in Chrome to see detailed statistics

## How It Works

1. When you visit a Reddit post, the Chrome extension detects it
2. Comments are sent to the local backend server for analysis
3. The server analyzes toxicity using advanced algorithms
4. Visual badges appear next to toxic comments
5. All data is processed locally - nothing is sent to external servers

## Troubleshooting

### Backend Server Won't Start

**Problem:** "Python is not installed or not in PATH"
- **Solution:** Install Python and make sure to check "Add Python to PATH" during installation

**Problem:** "Failed to install dependencies"
- **Solution:** Check your internet connection and try again

**Problem:** Port 8000 is already in use
- **Solution:** Close any other applications using port 8000, or restart your computer

### Chrome Extension Issues

**Problem:** Extension doesn't appear
- **Solution:** Make sure you selected the `chrome-extension` folder (not the main TrustLens folder)

**Problem:** Badges don't appear on Reddit
- **Solution:**
  1. Make sure the backend server is running
  2. Refresh the Reddit page
  3. Check that you're on a Reddit post page (not the homepage)

**Problem:** CORS or connection errors
- **Solution:**
  1. Verify the server is running at http://127.0.0.1:8000
  2. Visit http://127.0.0.1:8000/health in your browser - you should see `{"status":"healthy"}`

## Folder Structure

```
TrustLens/
├── START_TRUSTLENS.bat    # One-click server startup (DOUBLE-CLICK THIS)
├── api/                    # Backend server files
│   ├── main.py            # Main API server
│   ├── evidence.py        # Evidence detection
│   └── toxicity_model/    # Toxicity analysis models
├── chrome-extension/       # Chrome extension files
│   ├── manifest.json      # Extension configuration
│   ├── content.js         # Main extension script
│   ├── popup.html         # Extension popup
│   └── icon48.png         # Extension icon
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Stopping TrustLens

1. To stop the backend server: Press `CTRL+C` in the server window
2. To disable the extension: Go to `chrome://extensions/` and toggle off TrustLens

## Privacy & Security

- **All analysis is done locally** on your computer
- **No data is sent to external servers**
- **No personal information is collected**
- The backend server only runs on your machine (127.0.0.1)

## Support

If you encounter any issues:
1. Check the Troubleshooting section above
2. Make sure both the backend server and Chrome extension are running
3. Try restarting the backend server
4. Try reloading the Chrome extension

## Technical Details

- **Backend:** Python FastAPI server
- **Frontend:** Chrome Extension (Manifest V3)
- **Analysis:** Local toxicity detection models
- **API Endpoint:** http://127.0.0.1:8000

## License

MIT License - See LICENSE file for details

---

**Enjoy safer Reddit browsing with TrustLens!**
