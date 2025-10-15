# Reddit Post JSON Ingest

Minimal Chrome (MV3) content script that, when you open a Reddit post, collects the post metadata + comments and sends it as JSON to a local FastAPI endpoint (`/ingest`). The FastAPI server simply prints the payload.

## Components

- `manifest.json` – Declares a single content script (`content.js`) for `*.reddit.com/*`.
- `content.js` – Detects navigation to a Reddit post URL, fetches the post + comments via the public `.json?raw_json=1` endpoint, then POSTs a JSON payload to `http://127.0.0.1:8000/ingest`.
- `api/main.py` – FastAPI app exposing `/ingest` (POST) and `/health` (GET). `/ingest` prints the received payload to stdout.
- `requirements.txt` – Python dependencies (FastAPI, Uvicorn).

## Run the FastAPI server

Install dependencies (prefer a virtual environment):

```powershell
pip install -r requirements.txt
```

Run the server:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Health check:

Navigate to http://127.0.0.1:8000/health should return `{ "status": "healthy" }`.

## Load the extension in Chrome

1. Open `chrome://extensions`.
2. Enable "Developer mode" (toggle top-right).
3. Click "Load unpacked" and select the `red-dot-extension` folder.
4. Navigate to a Reddit post URL (e.g., `https://www.reddit.com/r/.../comments/...`).
5. Watch the terminal running Uvicorn—when a new post is first processed you'll see the JSON printed.

## How it works

- A polling loop (`URL_CHECK_INTERVAL_MS` = 2000 ms) watches for URL changes on Reddit (client-side navigation).
- When a new post URL is detected, it fetches `<post_url>.json?raw_json=1`.
- It extracts key fields: id, title, subreddit, author, permalink, url, selftext, score, num_comments, created_utc, and a simplified recursive comment tree (id, parent_id, author, body, score, depth, created_utc, permalink, replies).
- Sends `{ filename: <sanitized title or id>, data: { ... } }` to the API.
- Same post URL won't be resent unless you navigate away and back (URL must change).

## Adjustments

- To change the API base, edit `API_BASE` near the top of `content.js`.
- To resend on refresh even if URL unchanged, clear `lastProcessedPostUrl` logic or force a manual call to `processPost()`.
- CORS is currently permissive (`*`). Tighten in `api/main.py` if exposing publicly.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| No data printed | Server not running or wrong port | Start server / adjust `API_BASE` |
| CORS error in console | Browser blocked request | Ensure server running at 127.0.0.1:8000 with CORS `*` |
| JSON printed multiple times | Rapid navigation or history back triggers | This is expected; add debounce if needed |

## Next Steps (optional)

- Persist data to a database instead of printing.
- Add filtering or transformation logic server-side.
- Add a manual trigger (e.g., action button) instead of automatic.
- Implement authentication / restrict origins.

MIT License (add a LICENSE file if you need formal licensing).
