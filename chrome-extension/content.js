const POST_URL_PATTERN = /reddit\.com\/r\/[^/]+\/comments\//i;
const URL_CHECK_INTERVAL_MS = 2000;
// Attempt primary port 8001 (if 8000 busy) then fallback to 8000.
const API_PORTS = [8001, 8000];
let resolvedApiBase = null;

let lastProcessedPostUrl = null;
let processingPromise = null;

// TrustLens Real-time Analysis Configuration
const TRUSTLENS_CONFIG = {
    enableRealTimeBadges: true,
    enablePostAnalysis: true,
    badgeThreshold: 0.5,
    maxConcurrentAnalysis: 5
};

let trustLensBadgeManager = null;
let analysisQueue = [];
let activeAnalysis = 0;

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
    console.log("TrustLens: Sending to /ingest at:", base);
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
            console.error("TrustLens: /ingest responded with error:", res.status);
        } else {
            console.log("TrustLens: Successfully sent to /ingest!");
        }
    } catch (e) {
        if (e.name === 'AbortError') {
            console.error("TrustLens: /ingest request timed out");
        } else {
            console.error("TrustLens: Failed to reach /ingest API:", e);
        }
    } finally {
        clearTimeout(timeout);
    }
}

async function processPost(postUrl) {
    if (processingPromise) {
        console.log("TrustLens: Already processing, skipping...");
        return processingPromise;
    }

    console.log("TrustLens: Starting post processing for:", postUrl);
    processingPromise = (async () => {
        const payload = await buildPostPayload(postUrl);
        if (!payload) {
            console.log("TrustLens: Failed to build payload");
            return;
        }
        console.log("TrustLens: Payload built, sending to API...");
        await sendToApi(payload);
        lastProcessedPostUrl = postUrl;
        console.log("TrustLens: Post processing complete");
    })().finally(() => { processingPromise = null; });

    return processingPromise;
}

// Vector injection removed per simplification.

function monitorUrlChanges() {
    console.log("TrustLens: URL monitoring started");
    const checkUrl = () => {
        const postUrl = getCanonicalPostUrl();
        console.log("TrustLens: Checking URL, found:", postUrl);

        if (!postUrl) {
            console.log("TrustLens: Not a post URL, skipping");
            lastProcessedPostUrl = null;
            return;
        }
        if (postUrl === lastProcessedPostUrl) {
            console.log("TrustLens: Already processed this URL");
            return;
        }
        console.log("TrustLens: New post detected, triggering processing");
        void processPost(postUrl);
    };

    checkUrl();
    window.setInterval(checkUrl, URL_CHECK_INTERVAL_MS);
}

// TrustLens Real-time Analysis Functions
async function initializeTrustLens() {
    if (!TRUSTLENS_CONFIG.enableRealTimeBadges) return;
    
    try {
        console.log('TrustLens: Initializing badge system...');
        
        // Initialize the badge manager directly (no need to inject script)
        if (typeof ToxicityBadgeManager !== 'undefined') {
            window.trustLensBadgeManager = new ToxicityBadgeManager();
            console.log('TrustLens: Badge manager initialized');
        } else {
            console.log('TrustLens: Badge manager class not available, will initialize later');
        }
        
    } catch (error) {
        console.error('TrustLens: Failed to initialize badge system', error);
    }
}

async function analyzeCommentRealTime(commentText, commentId) {
    if (activeAnalysis >= TRUSTLENS_CONFIG.maxConcurrentAnalysis) {
        analysisQueue.push({ commentText, commentId });
        return;
    }
    
    activeAnalysis++;
    
    try {
        const apiBase = await resolveApiBaseOnce();
        const response = await fetch(`${apiBase}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ texts: [commentText] })
        });
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const result = await response.json();
        
        // Send result to badge manager
        if (window.trustLensBadgeManager) {
            window.trustLensBadgeManager.handleAnalysisResult(commentId, result);
        }
        
    } catch (error) {
        console.error('TrustLens: Real-time analysis failed', error);
        if (window.trustLensBadgeManager) {
            window.trustLensBadgeManager.handleAnalysisError(commentId, error);
        }
    } finally {
        activeAnalysis--;
        
        // Process queued analyses
        if (analysisQueue.length > 0) {
            const next = analysisQueue.shift();
            analyzeCommentRealTime(next.commentText, next.commentId);
        }
    }
}

function setupRealTimeCommentObserver() {
    if (!TRUSTLENS_CONFIG.enableRealTimeBadges) return;
    
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    processNewCommentsForAnalysis(node);
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Process existing comments
    processExistingCommentsForAnalysis();
}

function processNewCommentsForAnalysis(container) {
    const comments = container.querySelectorAll('[data-testid="comment"]');
    comments.forEach(comment => processCommentForAnalysis(comment));
}

function processExistingCommentsForAnalysis() {
    const comments = document.querySelectorAll('[data-testid="comment"]');
    comments.forEach(comment => processCommentForAnalysis(comment));
}

function processCommentForAnalysis(commentElement) {
    const commentId = extractCommentIdFromElement(commentElement);
    if (!commentId) return;

    const commentText = extractCommentTextFromElement(commentElement);
    if (!commentText || commentText.trim().length === 0) return;

    // Check if already analyzed
    if (window.trustLensBadgeManager && window.trustLensBadgeManager.isAnalyzed(commentId)) {
        return;
    }

    // Queue for analysis
    analyzeCommentRealTime(commentText, commentId);
}

function extractCommentIdFromElement(commentElement) {
    const idAttr = commentElement.getAttribute('id');
    if (idAttr && idAttr.startsWith('t1_')) return idAttr;
    
    const dataId = commentElement.getAttribute('data-permalink');
    if (dataId) return dataId.split('/').pop();
    
    return null;
}

function extractCommentTextFromElement(commentElement) {
    const textSelectors = [
        '[data-testid="comment"] p',
        '.usertext-body p',
        '[data-testid="comment"] .md',
        '.comment .usertext-body'
    ];
    
    for (const selector of textSelectors) {
        const textElement = commentElement.querySelector(selector);
        if (textElement) {
            return textElement.textContent.trim();
        }
    }
    
    return null;
}

function init() {
    monitorUrlChanges();
    
    // Initialize TrustLens real-time analysis
    if (TRUSTLENS_CONFIG.enableRealTimeBadges) {
        // Wait a bit for the badge manager script to load
        setTimeout(() => {
            initializeTrustLens();
            setupRealTimeCommentObserver();
        }, 1000);
    }
}

// Removed Chrome runtime messaging.

let unloaded = false;
window.addEventListener('beforeunload', () => { unloaded = true; });

if (document.readyState === "complete" || document.readyState === "interactive") {
    if (!unloaded) init();
} else {
    document.addEventListener("DOMContentLoaded", () => { if (!unloaded) init(); }, { once: true });
}
