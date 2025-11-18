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
