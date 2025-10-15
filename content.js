const POST_URL_PATTERN = /reddit\.com\/r\/[^/]+\/comments\//i;
const URL_CHECK_INTERVAL_MS = 2000;
// Attempt primary port 8001 (if 8000 busy) then fallback to 8000.
const API_PORTS = [8001, 8000];
let resolvedApiBase = null;

let lastProcessedPostUrl = null;
let processingPromise = null;

function isPostUrl(url) {
    return POST_URL_PATTERN.test(url);
}

function getCanonicalPostUrl() {
    if (!isPostUrl(window.location.href)) {
        return null;
    }

    const canonicalLink = document.querySelector('link[rel="canonical"]');
    if (canonicalLink && canonicalLink.href) {
        return canonicalLink.href.replace(/\?.*$/, "");
    }

    return window.location.href.replace(/\?.*$/, "");
}

function buildJsonEndpoint(url) {
    const trimmed = url.replace(/\?.*$/, "");
    const withSlash = trimmed.endsWith("/") ? trimmed : `${trimmed}/`;
    return `${withSlash}.json?raw_json=1`;
}

function transformComments(children) {
    if (!Array.isArray(children)) {
        return [];
    }

    const results = [];

    for (const child of children) {
        if (!child || child.kind !== "t1" || !child.data) {
            continue;
        }

        const data = child.data;
        const repliesSource = typeof data.replies === "object"
            ? data.replies?.data?.children || []
            : [];

        results.push({
            id: data.id,
            parent_id: data.parent_id,
            author: data.author,
            body: data.body,
            score: data.score,
            depth: data.depth,
            created_utc: data.created_utc,
            permalink: data.permalink
                ? `https://www.reddit.com${data.permalink}`
                : undefined,
            replies: transformComments(repliesSource),
        });
    }

    return results;
}

async function buildPostPayload(postUrl) {
    try {
        const endpoint = buildJsonEndpoint(postUrl);
        const response = await fetch(endpoint, { credentials: "include" });

        if (!response.ok) {
            throw new Error(`Request failed with status ${response.status}`);
        }

        const json = await response.json();
        const postListing = json?.[0]?.data?.children?.[0]?.data;
        const commentsListing = json?.[1]?.data?.children;

        if (!postListing) {
            throw new Error("Unable to locate post details");
        }

        return {
            filename: postListing.title || postListing.id,
            data: {
                id: postListing.id,
                title: postListing.title,
                subreddit: postListing.subreddit,
                author: postListing.author,
                permalink: postListing.permalink
                    ? `https://www.reddit.com${postListing.permalink}`
                    : postUrl,
                url: postListing.url,
                description: postListing.selftext,
                created_utc: postListing.created_utc,
                score: postListing.score,
                num_comments: postListing.num_comments,
                comments: transformComments(commentsListing),
            },
        };
    } catch (error) {
        console.error("Reddit Dot: unable to build post payload", error);
        return null;
    }
}

async function resolveApiBaseOnce() {
    if (resolvedApiBase) return resolvedApiBase;
    for (const port of API_PORTS) {
        const candidate = `http://127.0.0.1:${port}`;
        try {
            const r = await fetch(`${candidate}/health`, { method: "GET" });
            if (r.ok) {
                resolvedApiBase = candidate;
                return resolvedApiBase;
            }
        } catch (_) {
            // try next
        }
    }
    // Default to first even if unreachable; sends will fail gracefully.
    resolvedApiBase = `http://127.0.0.1:${API_PORTS[0]}`;
    return resolvedApiBase;
}

async function sendToApi(payload) {
    const base = await resolveApiBaseOnce();
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
        const res = await fetch(`${base}/ingest`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            signal: controller.signal,
        });
        if (!res.ok) {
            console.error("Reddit Ingest: server responded", res.status);
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            console.error("Reddit Ingest: request timed out");
        } else {
            console.error("Reddit Ingest: failed to reach API", e);
        }
    } finally {
        clearTimeout(timeout);
    }
}

async function processPost(postUrl) {
    if (processingPromise) return processingPromise;

    processingPromise = (async () => {
        const payload = await buildPostPayload(postUrl);
        if (!payload) return;
        await sendToApi(payload);
        lastProcessedPostUrl = postUrl;
    })().finally(() => { processingPromise = null; });

    return processingPromise;
}

// Vector injection removed per simplification.

function monitorUrlChanges() {
    const checkUrl = () => {
        const postUrl = getCanonicalPostUrl();

        if (!postUrl) { lastProcessedPostUrl = null; return; }
        if (postUrl === lastProcessedPostUrl) return;
        void processPost(postUrl);
    };

    checkUrl();
    window.setInterval(checkUrl, URL_CHECK_INTERVAL_MS);
}

function init() {
    monitorUrlChanges();
}

// Removed Chrome runtime messaging.

let unloaded = false;
window.addEventListener('beforeunload', () => { unloaded = true; });

if (document.readyState === "complete" || document.readyState === "interactive") {
    if (!unloaded) init();
} else {
    document.addEventListener("DOMContentLoaded", () => { if (!unloaded) init(); }, { once: true });
}
