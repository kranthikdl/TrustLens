// Single source of truth for the TrustLens API base URL.
// Override at extension build/load time if pointing at a non-default host.
const API_BASE = "http://localhost:8000";
const TRUST_CALCULATE_PATH = "/api/trust/calculate";

async function calculateTrust(payload) {
  const url = `${API_BASE}${TRUST_CALCULATE_PATH}`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    const error = new Error(`HTTP ${response.status}`);
    error.status = response.status;
    error.body = text;
    throw error;
  }

  return response.json();
}

function sanitizeFilename(name) {
  if (!name) {
    return "reddit_post";
  }

  const cleaned = name
    .replace(/[\\/:*?"<>|]/g, "")
    .replace(/\s+/g, "_")
    .trim();

  if (!cleaned) {
    return "reddit_post";
  }

  return cleaned.slice(0, 120);
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message && message.type === "CALCULATE_TRUST") {
    calculateTrust(message.payload || {})
      .then((data) => sendResponse({ data }))
      .catch((err) => {
        console.error("TrustLens: CALCULATE_TRUST failed", err);
        sendResponse({ error: "NETWORK", detail: err && err.message });
      });
    return true;
  }

  if (!message || message.type !== "SAVE_POST_JSON") {
    return;
  }

  const payload = message.payload || {};
  const baseName = sanitizeFilename(payload.filename);
  const data = payload.data;

  if (!data) {
    sendResponse({ success: false, error: "Missing data payload" });
    return;
  }

  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const objectUrl = URL.createObjectURL(blob);
  const downloadFilename = baseName.endsWith(".json")
    ? baseName
    : `${baseName}.json`;

  chrome.downloads.download(
    {
      url: objectUrl,
      filename: downloadFilename,
      saveAs: false,
    },
    (downloadId) => {
      const lastError = chrome.runtime.lastError;

      if (lastError) {
        sendResponse({ success: false, error: lastError.message });
      } else {
        sendResponse({ success: true, downloadId });
      }

      setTimeout(() => {
        URL.revokeObjectURL(objectUrl);
      }, 1000);
    }
  );

  return true;
});

// Test-only export. Guarded so the extension service worker never sees `module`.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    API_BASE,
    TRUST_CALCULATE_PATH,
    calculateTrust,
    sanitizeFilename,
  };
}
