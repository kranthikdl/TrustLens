(function () {
  if (window.trustLensRobustInitialized) {
    console.log("TrustLens: Already initialized, skipping...");
    return;
  }
  window.trustLensRobustInitialized = true;

  const API_BASE = "http://127.0.0.1:8000";

  class DuplicateProofManager {
    constructor() {
      this.processedCommentIds = new Set();
      this.processing = new Map();
      this.debugMode = false;
      this.currentAnalysisData = null;
      this.ROOT_SELECTOR =
        'article[data-testid="comment"], [id^="t1_"], .Comment, .comment.thing, .thing[data-type="comment"]';
      this.init();
    }

    init() {
      this.injectStyles();
      this.addDebugPanel();
      this.createSidebar();
      this.observe();
      setTimeout(() => this.scan(), 800);
      setTimeout(() => this.testAPI(), 400);
    }

    injectStyles() {
      if (document.getElementById("trustlens-dup-styles")) return;
      const style = document.createElement("style");
      style.id = "trustlens-dup-styles";
      style.textContent = `
       .trustlens-badge{display:inline-block;width:344px;height:100px;padding:16px;border-radius:0;font:600 11px system-ui,sans-serif;margin-right:8px;border:16px solid rgba(0,0,0,.1);box-sizing:content-box;position:relative;cursor:pointer}
       .trustlens-badge.trustlens-inline{width:auto !important;height:auto !important;padding:3px 8px !important;margin-right:8px;vertical-align:middle;line-height:1;font-size:11px !important;}
       .trustlens-user-row{display:flex;align-items:center;justify-content:space-between;gap:8px}
       .trustlens-safe{background:#d4edda;color:#155724}
       .trustlens-low{background:#fff3cd;color:#856404}
       .trustlens-medium{background:#f8d7da;color:#721c24}
       .trustlens-high{background:#d1ecf1;color:#0c5460}
       .trustlens-severe{background:#f5c6cb;color:#721c24}
      .trustlens-toxic{background:transparent;color:inherit}
      .trustlens-mild{background:transparent;color:inherit}
      .trustlens-neutral{background:transparent;color:inherit}
       .trustlens-loading{background:#f8f9fa;color:#6c757d}
      
       .trustlens-popup {
         position: absolute;
         z-index: 10000;
         background: white;
         border: 1px solid #e0e0e0;
         border-radius: 8px;
         padding: 14px 8px 4px 8px;
         box-shadow: 0 4px 12px rgba(0,0,0,0.15);
         max-width: 374px;
         font-family: system-ui, -apple-system, sans-serif;
         font-size: 13px;
         line-height: 0.5;
         color: #333;
         display: none;
         pointer-events: auto;
         margin-top: 8px;
       }
      
       .trustlens-popup.show {
         display: block;
       }
      
       .trustlens-popup-title {
         font-weight: 500;
         font-size: 10px;
         color: #07BEB8;
       }
      
       .trustlens-popup-section {
         display:flex;
         gap:2px;
       }
      
       .trustlens-popup-section:last-child {
         margin-bottom: 0;
       }
      
       .trustlens-popup-label {
         font-weight: 600;
         color: #666;
         margin-bottom: 2px;
       }
      
       .trustlens-popup-value {
         color: #1a1a1a;
       }
      
       .trustlens-popup-link {
         color: #07BEB8;
         text-decoration: underline;
         text-decoration-color: #07BEB8;
         font-weight: 500;
         margin-top: 8px;
         display: inline-block;
         cursor: pointer;
       }
      
       .trustlens-popup-link:hover {
         text-decoration: underline;
         text-decoration-color: #07BEB8;
       }
      
       /* Sidebar styles */
       .trustlens-sidebar {
         position: fixed;
         top: 0;
         right: -420px;
         width: 420px;
         height: 100vh;
         background: white;
         box-shadow: -2px 0 12px rgba(0,0,0,0.15);
         z-index: 10001;
         transition: right 0.3s ease-in-out;
         overflow-y: auto;
         font-family: system-ui, -apple-system, sans-serif;
       }
      
       .trustlens-sidebar.open {
         right: 0;
       }
      
       .trustlens-sidebar-header {
         padding: 20px;
         border-bottom: 1px solid #e0e0e0;
         display: flex;
         justify-content: space-between;
         align-items: flex-start;
         position: sticky;
         top: 0;
         background: white;
         z-index: 10;
       }
      
       .trustlens-sidebar-header-text {
         flex: 1;
       }
      
       .trustlens-sidebar-title {
         font-size: 16px;
         font-weight: 600;
         color: #1a1a1a;
         margin-bottom: 4px;
       }
      
       .trustlens-sidebar-subtitle {
         font-size: 14px;
         color: #1a1a1a;
         font-weight: 500;
       }
      
       .trustlens-sidebar-close {
         background: none;
         border: none;
         font-size: 24px;
         color: #666;
         cursor: pointer;
         padding: 0;
         width: 32px;
         height: 32px;
         display: flex;
         align-items: center;
         justify-content: center;
         border-radius: 4px;
         flex-shrink: 0;
       }
      
       .trustlens-sidebar-close:hover {
         background: #f5f5f5;
       }
      
       .trustlens-sidebar-content {
         padding: 20px;
       }
      
       .trustlens-sidebar-section {
         margin-bottom: 28px;
       }
      
       .trustlens-sidebar-section-title {
         font-size: 14px;
         font-weight: 600;
         color: #1a1a1a;
         margin-bottom: 16px;
       }
      
       .trustlens-sidebar-link {
         color: #0066cc;
         text-decoration: none;
         font-size: 13px;
         display: inline-block;
         margin-bottom: 16px;
       }
      
       .trustlens-sidebar-link:hover {
         text-decoration: underline;
       }
      
       .trustlens-metric {
         margin-bottom: 16px;
       }
      
       .trustlens-metric:last-child {
         margin-bottom: 0;
       }
      
       .trustlens-metric-header {
         display: flex;
         justify-content: space-between;
         align-items: center;
         margin-bottom: 6px;
       }
      
       .trustlens-metric-label {
         font-size: 13px;
         color: #333;
         font-weight: 500;
       }
      
       .trustlens-metric-value {
         font-size: 13px;
         color: #666;
         font-weight: 600;
       }
      
       .trustlens-metric-bar {
         width: 100%;
         height: 8px;
         background: #f0f0f0;
         border-radius: 4px;
         overflow: hidden;
       }
      
       .trustlens-metric-fill {
         height: 100%;
         border-radius: 4px;
         transition: width 0.3s ease;
       }
      
       .trustlens-metric-fill.tone {
         background: #4CAF50;
       }
      
       .trustlens-metric-fill.toxicity {
         background: #2196F3;
       }
      
       .trustlens-metric-fill.hostility {
         background: #00BCD4;
       }
      
       .trustlens-metric-fill.credibility {
         background: #03A9F4;
       }
      
       .trustlens-tags {
         display: flex;
         flex-wrap: wrap;
         gap: 8px;
       }
      
       .trustlens-tag {
         display: inline-block;
         padding: 6px 12px;
         background: #f5f5f5;
         border-radius: 16px;
         font-size: 12px;
         color: #333;
         border: 1px solid #e0e0e0;
       }
      
       .trustlens-color-legend {
         display: flex;
         flex-direction: column;
         gap: 12px;
       }
      
       .trustlens-color-item {
         display: flex;
         align-items: flex-start;
         gap: 12px;
       }
      
       .trustlens-color-dot {
         width: 12px;
         height: 12px;
         border-radius: 50%;
         flex-shrink: 0;
         margin-top: 3px;
       }
      
       .trustlens-color-dot.green {
         background: #4CAF50;
       }
      
       .trustlens-color-dot.yellow {
         background: #FFC107;
       }
      
       .trustlens-color-dot.red {
         background: #F44336;
       }
      
       .trustlens-color-text {
         flex: 1;
       }
      
       .trustlens-color-title {
         font-size: 13px;
         font-weight: 600;
         color: #1a1a1a;
         margin-bottom: 2px;
       }
      
       .trustlens-color-desc {
         font-size: 12px;
         color: #666;
         line-height: 1.4;
       }
      
       .trustlens-feedback {
         padding: 16px;
         background: #f9f9f9;
         border-radius: 8px;
         text-align: center;
       }
      
       .trustlens-feedback-title {
         font-size: 13px;
         color: #333;
         margin-bottom: 12px;
         font-weight: 500;
       }
      
       .trustlens-feedback-buttons {
         display: flex;
         justify-content: center;
         gap: 16px;
       }
      
       .trustlens-feedback-btn {
         background: white;
         border: 1px solid #e0e0e0;
         border-radius: 4px;
         padding: 8px 16px;
         cursor: pointer;
         font-size: 13px;
         color: #333;
         display: flex;
         align-items: center;
         gap: 6px;
       }
      
       .trustlens-feedback-btn:hover {
         background: #f5f5f5;
       }
      
       .trustlens-sidebar-overlay {
         position: fixed;
         top: 0;
         left: 0;
         width: 100%;
         height: 100%;
         background: rgba(0,0,0,0.3);
         z-index: 10000;
         display: none;
       }
      
       .trustlens-sidebar-overlay.show {
         display: block;
       }
      
       .trustlens-debug{position:fixed;top:10px;left:10px;z-index:10000;background:rgba(0,0,0,.85);color:#fff;padding:10px 12px;border-radius:6px;font:12px/1.3 ui-monospace,Menlo,monospace;min-width:210px}
       .trustlens-debug button{margin-top:6px;margin-right:6px;padding:3px 6px;border:0;border-radius:4px;background:#2d6cdf;color:#fff;cursor:pointer}
     `;
      document.head.appendChild(style);
    }

    createSidebar() {
      // Create overlay
      const overlay = document.createElement("div");
      overlay.className = "trustlens-sidebar-overlay";
      overlay.id = "trustlens-sidebar-overlay";
      overlay.addEventListener("click", () => this.closeSidebar());
      document.body.appendChild(overlay);

      // Create sidebar
      const sidebar = document.createElement("div");
      sidebar.className = "trustlens-sidebar";
      sidebar.id = "trustlens-sidebar";

      sidebar.innerHTML = `
       <div class="trustlens-sidebar-header">
         <div class="trustlens-sidebar-header-text">
           <div class="trustlens-sidebar-title">New to |</div>
           <div class="trustlens-sidebar-subtitle">Analysis Breakdown</div>
         </div>
         <button class="trustlens-sidebar-close" id="trustlens-sidebar-close">×</button>
       </div>
       <div class="trustlens-sidebar-content" id="trustlens-sidebar-content">
         <!-- Content will be populated dynamically -->
       </div>
     `;

      document.body.appendChild(sidebar);

      document
        .getElementById("trustlens-sidebar-close")
        .addEventListener("click", () => this.closeSidebar());
    }

    openSidebar(level, badgeColor, badgeData = null) {
      const sidebar = document.getElementById("trustlens-sidebar");
      const overlay = document.getElementById("trustlens-sidebar-overlay");
      const content = document.getElementById("trustlens-sidebar-content");

      content.innerHTML = this.getSidebarContent(level, badgeColor, badgeData);

      overlay.classList.add("show");
      sidebar.classList.add("open");
    }

    closeSidebar() {
      const sidebar = document.getElementById("trustlens-sidebar");
      const overlay = document.getElementById("trustlens-sidebar-overlay");

      overlay.classList.remove("show");
      sidebar.classList.remove("open");
    }

    getSidebarContent(level, badgeColor, badgeData = null) {
      const evidence = badgeData?.evidence || {};
      const status = badgeData?.status || "None";
      const urls = evidence.urls || [];
      const results = evidence.results || [];

      const verifiedCount = results.filter((r) => r.verified).length;
      const totalCount = results.length;
      const verifiedPercentage =
        totalCount > 0 ? Math.round((verifiedCount / totalCount) * 100) : 0;

      const credibilityMap = {
        Verified: 85,
        Mixed: 50,
        Unverified: 20,
        None: 30,
      };

      const credibility = credibilityMap[status] || 30;
      const reachability = verifiedPercentage;
      const sourceQuality =
        verifiedCount > 0 ? Math.min(90, verifiedCount * 30) : 0;

      let tags = [];
      if (status === "Verified") {
        tags = [
          "verified sources",
          "reachable links",
          "credible evidence",
          "fact-checked",
        ];
        if (results.length > 0) {
          const categories = [
            ...new Set(
              results.filter((r) => r.verified).map((r) => r.category)
            ),
          ];
          tags.push(...categories.slice(0, 2));
        }
      } else if (status === "Unverified") {
        tags = [
          "unverified sources",
          "unreachable links",
          "unverified claims",
          "needs verification",
        ];
      } else if (status === "Mixed") {
        tags = [
          "mixed evidence",
          "partial verification",
          "some sources verified",
          "needs review",
        ];
      } else {
        tags = [
          "no sources",
          "opinion only",
          "no evidence",
          "personal viewpoint",
        ];
      }

      const referencedSites = results
        .filter((r) => r.verified && r.domain)
        .map((r) => r.domain)
        .filter((v, i, a) => a.indexOf(v) === i)
        .slice(0, 5);

      let referencedSitesHTML = "";
      if (referencedSites.length > 0) {
        referencedSitesHTML = referencedSites
          .map((domain) => {
            const result = results.find(
              (r) => r.domain === domain && r.verified
            );
            const url = result
              ? result.final_url || result.normalized_url
              : `https://${domain}`;
            return `<a href="${url}" target="_blank" class="trustlens-sidebar-link">${domain}</a>`;
          })
          .join("");
      } else {
        referencedSitesHTML =
          '<span style="color: #666; font-size: 13px;">No verified sources found</span>';
      }

      const statusDescriptions = {
        Verified: "All sources verified and reachable.",
        Unverified: "Sources could not be verified or are unreachable.",
        Mixed: "Some sources verified, some not.",
        None: "No sources or links detected in this comment.",
      };

      return `
      <a href="#" class="trustlens-sidebar-link">Why am I seeing this?</a>
      
      <div class="trustlens-sidebar-section">
        <div class="trustlens-sidebar-section-title">Evidence Analysis</div>
        <div style="margin-bottom: 16px; padding: 12px; background: #f9f9f9; border-radius: 6px;">
          <div style="font-size: 14px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px;">
            Status: ${status}
          </div>
          <div style="font-size: 13px; color: #666; line-height: 1.4;">
            ${statusDescriptions[status] || "Evidence analysis complete."}
          </div>
          ${
            badgeData?.TL3_detail
              ? `<div style="font-size: 12px; color: #888; margin-top: 8px;">${badgeData.TL3_detail}</div>`
              : ""
          }
        </div>
        
        <div class="trustlens-metric">
          <div class="trustlens-metric-header">
            <span class="trustlens-metric-label">Credibility</span>
            <span class="trustlens-metric-value">${credibility}%</span>
          </div>
          <div class="trustlens-metric-bar">
            <div class="trustlens-metric-fill credibility" style="width: ${credibility}%"></div>
          </div>
        </div>
        
        ${
          totalCount > 0
            ? `
        <div class="trustlens-metric">
          <div class="trustlens-metric-header">
            <span class="trustlens-metric-label">Source Reachability</span>
            <span class="trustlens-metric-value">${reachability}%</span>
          </div>
          <div class="trustlens-metric-bar">
            <div class="trustlens-metric-fill tone" style="width: ${reachability}%"></div>
          </div>
        </div>
        
        <div class="trustlens-metric">
          <div class="trustlens-metric-header">
            <span class="trustlens-metric-label">Source Quality</span>
            <span class="trustlens-metric-value">${sourceQuality}%</span>
          </div>
          <div class="trustlens-metric-bar">
            <div class="trustlens-metric-fill toxicity" style="width: ${sourceQuality}%"></div>
          </div>
        </div>
        `
            : ""
        }
        
      </div>
      
      <div class="trustlens-sidebar-section">
        <div class="trustlens-sidebar-section-title">Signals Scan</div>
        <div class="trustlens-tags">
          ${tags
            .map((tag) => `<span class="trustlens-tag">${tag}</span>`)
            .join("")}
        </div>
      </div>
      
      <div class="trustlens-sidebar-section">
        <div class="trustlens-sidebar-section-title">Color Indicators</div>
        <div class="trustlens-color-legend">
          <div class="trustlens-color-item">
            <div class="trustlens-color-dot green"></div>
            <div class="trustlens-color-text">
              <div class="trustlens-color-title">Green - Neutral & Verified</div>
              <div class="trustlens-color-desc">Neutral tone with verified sources or no evidence claims. Positive language with credible backing.</div>
            </div>
          </div>
          <div class="trustlens-color-item">
            <div class="trustlens-color-dot yellow"></div>
            <div class="trustlens-color-text">
              <div class="trustlens-color-title">Yellow - Mild or Unverified</div>
              <div class="trustlens-color-desc">Mild toxicity detected, or neutral tone with unverifiable evidence. Exercise caution.</div>
            </div>
          </div>
          <div class="trustlens-color-item">
            <div class="trustlens-color-dot red"></div>
            <div class="trustlens-color-text">
              <div class="trustlens-color-title">Red - Toxic Content</div>
              <div class="trustlens-color-desc">Toxic language detected (strong language, hostility, or personal attacks) regardless of evidence quality.</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="trustlens-sidebar-section">
        <div class="trustlens-sidebar-section-title">Referenced Sites</div>
        ${referencedSitesHTML}
      </div>
      
       <div class="trustlens-sidebar-section">
         <div class="trustlens-feedback">
           <div class="trustlens-feedback-title">Was this analysis helpful?</div>
           <div class="trustlens-feedback-buttons">
             <button class="trustlens-feedback-btn">
               👍 Helpful
             </button>
             <button class="trustlens-feedback-btn">
               👎 Not helpful
             </button>
           </div>
         </div>
       </div>
      
       <div class="trustlens-sidebar-section" style="font-size: 11px; color: #999; line-height: 1.5;">
         I got called as a psychopath once where they still keep liking... "I received feedback that may not be entirely pleasant."
       </div>
     `;
    }

    addDebugPanel() {
      if (!this.debugMode || document.getElementById("trustlens-debug")) return;
      const box = document.createElement("div");
      box.id = "trustlens-debug";
      box.className = "trustlens-debug";
      box.innerHTML = `
       <div><strong>TrustLens Debug</strong></div>
       <div>Comments found: <span id="tl-count">0</span></div>
       <div>Processed: <span id="tl-processed">0</span></div>
       <div>Badges visible: <span id="tl-badges">0</span></div>
       <div>API Status: <span id="tl-api">Testing...</span></div>
       <div>Last: <span id="tl-last">Init</span></div>
       <div>
         <button id="tl-scan">Scan Now</button>
         <button id="tl-clear">Clear All</button>
         <button id="tl-check">Check Duplicates</button>
       </div>
     `;
      document.body.appendChild(box);
      document.getElementById("tl-scan").onclick = () => this.scan();
      document.getElementById("tl-clear").onclick = () => this.clearAll();
      document.getElementById("tl-check").onclick = () =>
        this.checkDuplicates();

      setInterval(() => this.updateBadgeCount(), 1000);
    }

    updateBadgeCount() {
      const count = document.querySelectorAll(".trustlens-badge").length;
      this.update("tl-badges", String(count));
    }

    checkDuplicates() {
      const badges = document.querySelectorAll(
        ".trustlens-badge[data-comment-id]"
      );
      const ids = Array.from(badges).map((b) => b.dataset.commentId);
      const uniqueIds = new Set(ids);
      const duplicates = ids.length - uniqueIds.size;

      if (duplicates > 0) {
        console.warn(`TrustLens: Found ${duplicates} duplicate badges!`);
        this.update("tl-last", `⚠️ ${duplicates} duplicates found`);

        const counts = {};
        ids.forEach((id) => {
          counts[id] = (counts[id] || 0) + 1;
        });
        const dupIds = Object.keys(counts).filter((id) => counts[id] > 1);
        console.warn("Duplicate IDs:", dupIds);

        dupIds.forEach((id) => {
          const badgesWithId = Array.from(
            document.querySelectorAll(
              `.trustlens-badge[data-comment-id="${id}"]`
            )
          );
          badgesWithId.slice(1).forEach((b) => b.remove());
        });

        this.updateBadgeCount();
        this.update("tl-last", `Fixed ${duplicates} duplicates`);
      } else {
        this.update("tl-last", "No duplicates");
      }
    }

    update(field, value) {
      const el = document.getElementById(field);
      if (el) el.textContent = value;
    }

    observe() {
      const mo = new MutationObserver((muts) => {
        for (const m of muts) {
          for (const n of m.addedNodes) {
            if (n.nodeType !== Node.ELEMENT_NODE) continue;
            this.processNode(n);
          }
        }
      });
      mo.observe(document.body, { childList: true, subtree: true });
    }

    scan() {
      const roots = this.findRoots();
      this.update("tl-count", String(roots.length));
      this.update("tl-last", `Scan ${roots.length}`);
      roots.forEach((el, i) =>
        setTimeout(() => this.processComment(el), i * 50)
      );
      setTimeout(() => {
        this.update("tl-processed", String(this.processedCommentIds.size));
        this.updateBadgeCount();
      }, 1000);
    }

    clearAll() {
      document.querySelectorAll(".trustlens-badge").forEach((b) => b.remove());
      document.querySelectorAll(".trustlens-popup").forEach((p) => p.remove());
      this.processedCommentIds.clear();
      this.processing.clear();
      document.querySelectorAll(this.ROOT_SELECTOR).forEach((el) => {
        if (el.dataset) {
          delete el.dataset.trustlensProcessed;
          delete el.dataset.trustlensId;
        }
      });
      this.update("tl-last", "Cleared");
      this.update("tl-processed", "0");
      this.updateBadgeCount();
    }

    findRoots() {
      const nodes = Array.from(document.querySelectorAll(this.ROOT_SELECTOR));
      return nodes.filter((el) => el.closest(this.ROOT_SELECTOR) === el);
    }

    processNode(node) {
      const nodes = node.querySelectorAll(this.ROOT_SELECTOR);
      nodes.forEach((el) => {
        if (el.closest(this.ROOT_SELECTOR) === el) this.processComment(el);
      });
    }

    getId(el) {
      if (el.dataset && el.dataset.trustlensId) return el.dataset.trustlensId;
      const id = el.getAttribute("id");
      if (id && id.startsWith("t1_")) return (el.dataset.trustlensId = id);
      const permalink = el.getAttribute("data-permalink");
      if (permalink)
        return (el.dataset.trustlensId = permalink.split("/").pop());
      const fullname = el.getAttribute("data-fullname");
      if (fullname) return (el.dataset.trustlensId = fullname);
      return (el.dataset.trustlensId = `c_${Date.now()}_${Math.random()
        .toString(36)
        .slice(2)}`);
    }

    getText(el) {
      const trySel = [".md", ".usertext-body", '[data-testid="comment"]'];
      for (const s of trySel) {
        const n = el.querySelector(s);
        if (n && n.textContent && n.textContent.trim().length > 0) {
          let text = n.textContent.trim();

          const links = n.querySelectorAll("a[href]");
          const urls = new Set();
          links.forEach((link) => {
            const href = link.getAttribute("href");
            if (
              href &&
              (href.startsWith("http://") || href.startsWith("https://"))
            ) {
              urls.add(href);
            }
          });

          urls.forEach((url) => {
            if (!text.includes(url)) {
              text += " " + url;
            }
          });

          return text;
        }
      }
      let all = el.textContent.trim();

      const links = el.querySelectorAll("a[href]");
      const urls = new Set();
      links.forEach((link) => {
        const href = link.getAttribute("href");
        if (
          href &&
          (href.startsWith("http://") || href.startsWith("https://"))
        ) {
          urls.add(href);
        }
      });

      urls.forEach((url) => {
        if (!all.includes(url)) {
          all += " " + url;
        }
      });

      return all.length > 0 ? all : null;
    }

    async testAPI() {
      try {
        const r = await fetch(`${API_BASE}/health`);
        this.update("tl-api", r.ok ? "Connected" : "Error");
      } catch {
        this.update("tl-api", "Failed");
      }
    }

    getPopupContent(level, badgeColor, badgeData = null) {
      const getToxicityLevel = () => {
        if (level === "neutral" || badgeColor === "green") return "neutral";
        if (level === "toxic" || badgeColor === "red") return "toxic";
        if (level === "mild" || badgeColor === "yellow") return "mild";

        if (badgeData && badgeData.toxicity_color) {
          const color = badgeData.toxicity_color;
          if (color === "green") return "neutral";
          if (color === "red") return "toxic";
          if (color === "yellow") return "mild";
        }
        return "neutral";
      };

      const toxicityLevel = getToxicityLevel();

      const toneMessages = {
        neutral: "Positive tone detected",
        toxic: "Negative tone detected",
        mild: "Slightly strong tone detected",
      };

      const backgroundColors = {
        neutral: "#388E3C",
        toxic: "#D32F2F",
        mild: "#EDE246",
      };

      const status =
        (badgeData &&
          (badgeData.status ||
            (badgeData.evidence && badgeData.evidence.status))) ||
        "None";

      return {
        title: "TrustLens",
        toneMessage: toneMessages[toxicityLevel],
        backgroundColor: backgroundColors[toxicityLevel],
        status,
      };
    }

    createPopup(badge, level, badgeColor, badgeData = null) {
      document.querySelectorAll(".trustlens-popup").forEach((p) => p.remove());

      const popup = document.createElement("div");
      popup.className = "trustlens-popup";

      if (!badgeData && badge.dataset.evidenceStatus) {
        badgeData = {
          status: badge.dataset.evidenceStatus,
          TL2_tooltip: badge.dataset.evidenceTooltip || "",
          TL3_detail: badge.dataset.evidenceDetail || "",
          evidence: badge.dataset.evidenceData
            ? JSON.parse(badge.dataset.evidenceData)
            : {},
        };
      }

      const popupData = this.getPopupContent(level, badgeColor, badgeData);

      let statusDisplay = "";
      const status = popupData.status || "None";
      console.log("TrustLens Popup Status (from analyze_comment):", status);

      if (
        status === "Verified" ||
        status === "Mixed" ||
        status === "Unverified"
      ) {
        let borderColor = "#07BEB8";
        let bgColor = "#F5FFFE";
        let textColor = "#07BEB8";
        let iconColor = "#07BEB8";
        let iconPath = "";
        let displayText = "";

        if (status === "Verified") {
          borderColor = "#07BEB8";
          bgColor = "#F5FFFE";
          textColor = "#07BEB8";
          iconColor = "#07BEB8";
          displayText = "Valid URL";
          iconPath = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="none">
<path d="M9.14584 10.7918L7.50001 9.14592C7.37501 9.02092 7.22222 8.95842 7.04168 8.95842C6.86114 8.95842 6.70834 9.02092 6.58334 9.14592C6.45834 9.27092 6.39584 9.42371 6.39584 9.60425C6.39584 9.78479 6.45834 9.93759 6.58334 10.0626L8.64584 12.1459C8.77084 12.2709 8.91668 12.3334 9.08334 12.3334C9.25001 12.3334 9.39584 12.2709 9.52084 12.1459L13.3958 8.27092C13.5208 8.14592 13.5833 7.99663 13.5833 7.823C13.5833 7.64938 13.5208 7.50704 13.3958 7.39592C13.2847 7.28479 13.1389 7.23271 12.9583 7.23967C12.7778 7.24663 12.632 7.30563 12.5208 7.41675L9.14584 10.7918ZM10 18.2501C9.93055 18.2501 9.86459 18.2431 9.80209 18.2293C9.73959 18.2154 9.67363 18.1945 9.60418 18.1668C7.67364 17.514 6.14584 16.3438 5.02084 14.6563C3.89584 12.9688 3.33334 11.1181 3.33334 9.10425V5.02092C3.33334 4.75704 3.40973 4.51746 3.56251 4.30217C3.71529 4.08689 3.90973 3.93064 4.14584 3.83341L9.56251 1.81258C9.7153 1.75703 9.86114 1.72925 10 1.72925C10.1389 1.72925 10.2847 1.75703 10.4375 1.81258L15.8542 3.83341C16.0903 3.93064 16.2847 4.08689 16.4375 4.30217C16.5903 4.51746 16.6667 4.75704 16.6667 5.02092V9.10425C16.6667 11.1181 16.1042 12.9688 14.9792 14.6563C13.8542 16.3438 12.3264 17.514 10.3958 18.1668C10.3264 18.1945 10.2604 18.2154 10.1979 18.2293C10.1354 18.2431 10.0695 18.2501 10 18.2501Z" fill="#07BEB8"/>
</svg>`;
        } else if (status === "Unverified" || status === "Mixed") {
          borderColor = "#DC3545";
          bgColor = "#FFF5F5";
          textColor = "#F74343";
          iconColor = "#DC3545";
          displayText = "Invalid URL";
          iconPath = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 20 20" fill="none">
<path d="M10 10.729L11.5 12.1665C11.625 12.2915 11.7778 12.354 11.9583 12.354C12.1389 12.354 12.2917 12.2915 12.4167 12.1665C12.5556 12.0276 12.625 11.8679 12.625 11.6873C12.625 11.5068 12.5556 11.354 12.4167 11.229L10.9583 9.7915L12.4167 8.33317C12.5556 8.20817 12.625 8.05538 12.625 7.87484C12.625 7.69429 12.5556 7.53454 12.4167 7.39567C12.2917 7.27067 12.1389 7.20817 11.9583 7.20817C11.7778 7.20817 11.625 7.27067 11.5 7.39567L10 8.83317L8.50001 7.39567C8.37501 7.27067 8.22572 7.20471 8.05209 7.19775C7.87847 7.19079 7.72222 7.2568 7.58334 7.39567C7.45834 7.52067 7.39239 7.67692 7.38543 7.86442C7.37847 8.05192 7.44447 8.20817 7.58334 8.33317L9.04168 9.7915L7.58334 11.229C7.44447 11.354 7.37501 11.5068 7.37501 11.6873C7.37501 11.8679 7.44447 12.0276 7.58334 12.1665C7.70834 12.2915 7.86114 12.354 8.04168 12.354C8.22222 12.354 8.37501 12.2915 8.50001 12.1665L10 10.729ZM10 18.2498C9.93055 18.2498 9.86459 18.2429 9.80209 18.229C9.73959 18.2151 9.67364 18.1943 9.60418 18.1665C7.67364 17.5137 6.14584 16.3436 5.02084 14.6561C3.89584 12.9686 3.33334 11.1179 3.33334 9.104V5.02067C3.33334 4.7568 3.40973 4.51721 3.56251 4.30192C3.71529 4.08665 3.90973 3.9304 4.14584 3.83317L9.56251 1.81234C9.7153 1.75678 9.86114 1.729 10 1.729C10.1389 1.729 10.2847 1.75678 10.4375 1.81234L15.8542 3.83317C16.0903 3.9304 16.2847 4.08665 16.4375 4.30192C16.5903 4.51721 16.6667 4.7568 16.6667 5.02067V9.104C16.6667 11.1179 16.1042 12.9686 14.9792 14.6561C13.8542 16.3436 12.3264 17.5137 10.3958 18.1665C10.3264 18.1943 10.2604 18.2151 10.1979 18.229C10.1354 18.2429 10.0695 18.2498 10 18.2498Z" fill="#F74343"/>
</svg>`;
        }

        statusDisplay = `
    <div style="
      display:inline-flex;
      align-items:center;
      gap:2px;
      padding:3px 4px 3px 6px;
      font-size:12px;
      font-weight:500;
    ">
      ${iconPath}
      <span style="color:${textColor};">${displayText}</span>
    </div>
  `;
      }

      const statusDiv = status !== "None" && statusDisplay ? statusDisplay : "";

      popup.innerHTML = `
  <div class="trustlens-popup-title">${popupData.title}</div>
  <div style="display:flex; gap:2px;">
    <div style="padding: 6px; border-radius: 4px; background-color: ${popupData.backgroundColor}; color: white; text-align: center; font-weight: 500; margin: 8px 0;">
      <div style="display: flex; align-items: center; gap: 3px; justify-content: center; flex-wrap: wrap;">
        <!-- icon svg -->
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none">
<g clip-path="url(#clip0_448_1594)">
<path d="M12 24C15.1826 24 18.2348 22.7357 20.4853 20.4853C22.7357 18.2348 24 15.1826 24 12C24 8.8174 22.7357 5.76516 20.4853 3.51472C18.2348 1.26428 15.1826 0 12 0C8.8174 0 5.76516 1.26428 3.51472 3.51472C1.26428 5.76516 0 8.8174 0 12C0 15.1826 1.26428 18.2348 3.51472 20.4853C5.76516 22.7357 8.8174 24 12 24ZM17.2969 9.79688L11.2969 15.7969C10.8562 16.2375 10.1438 16.2375 9.70781 15.7969L6.70781 12.7969C6.26719 12.3562 6.26719 11.6438 6.70781 11.2078C7.14844 10.7719 7.86094 10.7672 8.29688 11.2078L10.5 13.4109L15.7031 8.20312C16.1437 7.7625 16.8562 7.7625 17.2922 8.20312C17.7281 8.64375 17.7328 9.35625 17.2922 9.79219L17.2969 9.79688Z" fill="#FDFBFB"/>
</g>
<defs>
<clipPath id="clip0_448_1594">
<rect width="24" height="24" fill="white"/>
</clipPath>
</defs>
</svg>
        <div>${popupData.toneMessage}</div>
      </div>
    </div>
    ${statusDiv}
  </div>
`;

      document.body.appendChild(popup);

      const badgeRect = badge.getBoundingClientRect();
      popup.style.left = `${badgeRect.left}px`;
      popup.style.top = `${badgeRect.bottom + window.scrollY}px`;

      return popup;
    }

    addHoverListeners(badge, level, badgeColor, badgeData = null) {
      let popup = null;
      let hideTimeout = null;

      const clearHideTimeout = () => {
        if (hideTimeout) {
          clearTimeout(hideTimeout);
          hideTimeout = null;
        }
      };

      const scheduleHide = () => {
        clearHideTimeout();
        hideTimeout = setTimeout(() => {
          if (popup) {
            popup.classList.remove("show");
            setTimeout(() => {
              if (popup && popup.parentElement) {
                popup.remove();
              }
              popup = null;
            }, 200);
          }
        }, 300);
      };

      badge.addEventListener("mouseenter", async () => {
        clearHideTimeout();

        let freshBadgeData = badgeData;
        const commentText = badge.dataset.commentText;

        if (commentText) {
          try {
            const res = await fetch(`${API_BASE}/analyze-evidence`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ text: commentText }),
            });

            if (res.ok) {
              const data = await res.json();
              console.log(
                "TrustLens: Fresh status fetched on hover:",
                data.status
              );

              freshBadgeData = {
                status: data.status || "None",
                badgeColor: data.badge_color || badgeColor,
                toxicity_color: data.toxicity_color || badgeColor,
                evidence: data.evidence || {},
                TL2_tooltip: data.TL2_tooltip || "",
                TL3_detail: data.TL3_detail || "",
              };
            }
          } catch (e) {
            console.warn(
              "TrustLens: Failed to fetch fresh status on hover:",
              e
            );
          }
        }

        popup = this.createPopup(badge, level, badgeColor, freshBadgeData);

        popup.addEventListener("mouseenter", () => {
          clearHideTimeout();
        });

        popup.addEventListener("mouseleave", () => {
          scheduleHide();
        });

        setTimeout(() => {
          if (popup) {
            popup.classList.add("show");
          }
        }, 100);
      });

      badge.addEventListener("mouseleave", () => {
        scheduleHide();
      });
    }

    async processComment(el) {
      if (!el) return;

      if (el.dataset.trustlensProcessed === "true") return;
      const parentProcessed = el.closest(`[data-trustlens-processed="true"]`);
      if (parentProcessed) return;

      const id = this.getId(el);
      if (!id) return;

      if (this.processedCommentIds.has(id)) {
        el.dataset.trustlensProcessed = "true";
        return;
      }

      if (this.processing.has(id)) return;

      const text = this.getText(el);
      if (!text) return;

      const textPreview =
        text.length > 100 ? text.substring(0, 100) + "..." : text;
      console.log(`TrustLens: Extracted text for comment ${id}:`, textPreview);
      console.log(
        `TrustLens: Text length: ${
          text.length
        }, Contains URL: ${/https?:\/\//.test(text)}`
      );

      this.processing.set(id, true);
      el.dataset.trustlensProcessed = "true";

      el.querySelectorAll(`[data-trustlens-id="${id}"]`).forEach((nested) => {
        nested.dataset.trustlensProcessed = "true";
      });

      el.querySelectorAll(`.trustlens-badge[data-comment-id="${id}"]`).forEach(
        (b) => b.remove()
      );
      el.querySelectorAll(".trustlens-badge").forEach((b) => {
        if (!b.dataset.commentId || b.dataset.commentId === id) b.remove();
      });

      this.insertBadge(el, id, "loading", "Analyzing...");

      try {
        const res = await fetch(`${API_BASE}/analyze-evidence`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        console.log("TrustLens: Evidence API response:", data);
        console.log("TrustLens: Evidence status:", data.status);
        console.log("TrustLens: Badge color:", data.badge_color);
        console.log("TrustLens: Toxicity color:", data.toxicity_color);

        const badgeColor = data.badge_color || "yellow";
        const evidenceStatus = (data.status || "None").trim();

        const evidenceData = data.evidence || {
          urls: data.urls || [],
          results: data.results || [],
        };

        const statusToLabel = {
          Verified: "Verified",
          Unverified: "Unverified",
          Mixed: "Mixed",
          None: "No Evidence",
          "Evidence present, unverified": "Mixed",
        };

        // Map badge color from API to level key (API now determines color based on toxicity + evidence)
        const colorToLevel = {
          red: "toxic",
          yellow: "mild",
          green: "neutral",
        };

        const displayText = statusToLabel[evidenceStatus] || "No Evidence";
        let levelKey = colorToLevel[badgeColor] || "mild";

        console.log("TrustLens: Badge color mapping", {
          evidenceStatus,
          badgeColor,
          levelKey,
          displayText,
          toxicityColor: data.toxicity_color,
        });

        const badgeData = {
          status: evidenceStatus,
          badgeColor: badgeColor,
          toxicity_color: data.toxicity_color || badgeColor,
          evidence: evidenceData,
          TL2_tooltip: data.TL2_tooltip || "",
          TL3_detail: data.TL3_detail || "",
        };

        this.insertBadge(
          el,
          id,
          levelKey,
          displayText,
          true,
          badgeColor,
          badgeData
        );
        this.processedCommentIds.add(id);
      } catch (e) {
        console.warn("TrustLens: evidence analysis failed", e);
        this.insertBadge(el, id, "mild", "Error");
      } finally {
        this.processing.delete(id);
        this.update("tl-processed", String(this.processedCommentIds.size));
        this.update("tl-last", `Done ${id}`);
        this.updateBadgeCount();
      }
    }

    pretty(level) {
      return level.charAt(0).toUpperCase() + level.slice(1);
    }

    levelFrom(preds, probs) {
      const maxProb = Math.max(...probs);
      const toxicCount = preds.reduce((s, p) => s + p, 0);
      if (maxProb < 0.5) return "safe";
      if (toxicCount >= 3 || probs[1] >= 0.7) return "severe";
      if (toxicCount >= 2 || maxProb >= 0.8) return "high";
      if (toxicCount >= 1 || maxProb >= 0.6) return "medium";
      return "low";
    }

    insertBadge(
      el,
      id,
      level,
      text,
      replace = false,
      badgeColor = null,
      badgeData = null
    ) {
      // Badge color is now determined by API (toxicity + evidence), so trust the level parameter
      console.log("TrustLens: insertBadge called", {
        id,
        level,
        text,
        replace,
        badgeColor,
        badgeData: badgeData
          ? {
              status: badgeData.status,
              badgeColor: badgeData.badgeColor,
            }
          : null,
      });

      const allExisting = el.querySelectorAll(
        `.trustlens-badge[data-comment-id="${id}"]`
      );
      if (allExisting.length > 0) {
        allExisting.forEach((b) => b.remove());
        if (!replace) return;
      }

      el.querySelectorAll(".trustlens-badge").forEach((b) => {
        if (!b.dataset.commentId || b.dataset.commentId === id) b.remove();
      });

      if (!replace && allExisting.length > 0) return;

      const labelMap = {
        toxic: "Unverified",
        mild: "Mixed",
        neutral: "Verified",
        safe: "Verified",
        warning: "Mixed",
        dangerous: "Unverified",
        loading: "Analyzing...",
      };

      const displayText =
        text && text !== "Analyzing..." ? text : labelMap[level] || "Unknown";

      const badge = document.createElement("span");
      badge.className = `trustlens-badge trustlens-${level}`;
      badge.dataset.commentId = id;
      const commentText = this.getText(el);
      if (commentText) {
        badge.dataset.commentText = commentText;
      }
      if (badgeData) {
        badge.dataset.evidenceStatus = badgeData.status;
        badge.dataset.evidenceTooltip = badgeData.TL2_tooltip || "";
        badge.dataset.evidenceDetail = badgeData.TL3_detail || "";
        badge.dataset.evidenceData = JSON.stringify(badgeData.evidence || {});
      }

      if (level === "neutral") {
        const clipId = `trustlens-neutral-clip-${id.replace(
          /[^a-zA-Z0-9]/g,
          "-"
        )}`;
        const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle;">
        <g clip-path="url(#${clipId})">
        <path d="M22.5714 9.25487V6.14286C22.5714 5.19609 21.8039 4.42857 20.8571 4.42857H18.9767C17.4197 4.42857 15.909 3.89865 14.6932 2.92595L12.2857 1L9.87827 2.92597C8.6624 3.89865 7.1517 4.42857 5.59465 4.42857H3.71429C2.76752 4.42857 2 5.19609 2 6.14286V9.25487C2 15.4859 6.24073 20.9173 12.2857 22.4286C18.3306 20.9173 22.5714 15.4859 22.5714 9.25487Z" stroke="#388E3C" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M15.7123 8.017C15.8884 7.85335 16.1227 7.76288 16.3659 7.76467C16.609 7.76647 16.8419 7.86039 17.0154 8.02662C17.1889 8.19285 17.2895 8.41839 17.2959 8.65564C17.3024 8.89289 17.2141 9.1233 17.0498 9.29825L12.0623 15.3872C11.9766 15.4774 11.8731 15.5498 11.758 15.6C11.6429 15.6502 11.5187 15.6773 11.3926 15.6796C11.2666 15.6819 11.1414 15.6593 11.0245 15.6133C10.9076 15.5672 10.8015 15.4987 10.7123 15.4116L7.40483 12.1829C7.31272 12.0991 7.23884 11.9981 7.1876 11.8858C7.13636 11.7735 7.10881 11.6524 7.10659 11.5295C7.10437 11.4066 7.12753 11.2845 7.17468 11.1706C7.22183 11.0566 7.29201 10.9531 7.38103 10.8662C7.47006 10.7793 7.5761 10.7108 7.69283 10.6648C7.80957 10.6187 7.93461 10.5961 8.06048 10.5983C8.18636 10.6005 8.3105 10.6274 8.4255 10.6774C8.5405 10.7274 8.644 10.7995 8.72983 10.8894L11.3473 13.4434L15.6886 8.04384L15.7123 8.017Z" fill="#388E3C"/>
        </g>
        <defs>
        <clipPath id="${clipId}">
        <rect width="24" height="23.4286" fill="white"/>
        </clipPath>
        </defs>
        </svg>`;
        badge.innerHTML = svgIcon;
      } else if (level === "toxic") {
        const clipId0 = `trustlens-toxic-clip0-${id.replace(
          /[^a-zA-Z0-9]/g,
          "-"
        )}`;
        const clipId1 = `trustlens-toxic-clip1-${id.replace(
          /[^a-zA-Z0-9]/g,
          "-"
        )}`;
        const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle;">
        <g clip-path="url(#${clipId0})">
        <path d="M22.5714 9.25487V6.14286C22.5714 5.19609 21.8039 4.42857 20.8571 4.42857H18.9767C17.4197 4.42857 15.909 3.89865 14.6932 2.92595L12.2857 1L9.87827 2.92597C8.6624 3.89865 7.1517 4.42857 5.59465 4.42857H3.71429C2.76752 4.42857 2 5.19609 2 6.14286V9.25487C2 15.4859 6.24073 20.9173 12.2857 22.4286C18.3306 20.9173 22.5714 15.4859 22.5714 9.25487Z" stroke="#ED0000" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
        <g clip-path="url(#${clipId1})">
        <path d="M12.0002 12.5894L9.27787 15.3186C9.15191 15.4436 9.00491 15.5061 8.83683 15.5061C8.66879 15.5061 8.52183 15.4436 8.396 15.3186C8.271 15.1936 8.2085 15.0478 8.2085 14.8811C8.2085 14.7144 8.271 14.5686 8.396 14.4436L11.1252 11.7144L8.396 9.01298C8.271 8.88702 8.2085 8.73998 8.2085 8.57194C8.2085 8.4039 8.271 8.25694 8.396 8.1311C8.521 8.0061 8.66683 7.9436 8.8335 7.9436C9.00016 7.9436 9.146 8.0061 9.271 8.1311L12.0002 10.8603L14.7016 8.1311C14.8137 8.0061 14.9572 7.9436 15.1322 7.9436C15.3072 7.9436 15.4577 8.0061 15.5835 8.1311C15.7085 8.2561 15.771 8.40194 15.771 8.5686C15.771 8.73527 15.7085 8.8811 15.5835 9.0061L12.8543 11.7144L15.5835 14.4367C15.7085 14.5627 15.771 14.7097 15.771 14.8778C15.771 15.0458 15.7085 15.1928 15.5835 15.3186C15.4585 15.4436 15.3127 15.5061 15.146 15.5061C14.9793 15.5061 14.8335 15.4436 14.7085 15.3186L12.0002 12.5894Z" fill="#ED0000"/>
        </g>
        </g>
        <defs>
        <clipPath id="${clipId0}">
        <rect width="24" height="23.4286" fill="white"/>
        </clipPath>
        <clipPath id="${clipId1}">
        <rect width="20" height="20" fill="white" transform="translate(2 1.71436)"/>
        </clipPath>
        </defs>
        </svg>`;
        badge.innerHTML = svgIcon;
      } else if (level === "mild") {
        const clipId = `trustlens-mild-clip-${id.replace(
          /[^a-zA-Z0-9]/g,
          "-"
        )}`;
        const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle;">
        <g clip-path="url(#${clipId})">
        <path d="M22.2858 9.54051V6.4285C22.2858 5.48174 21.5183 4.71422 20.5715 4.71422H18.6911C17.1341 4.71422 15.6234 4.1843 14.4075 3.21159L12.0001 1.28564L9.59263 3.21161C8.37676 4.1843 6.86606 4.71422 5.30901 4.71422H3.42864C2.48188 4.71422 1.71436 5.48174 1.71436 6.4285V9.54051C1.71436 15.7715 5.95509 21.2029 12.0001 22.7142C18.045 21.2029 22.2858 15.7715 22.2858 9.54051Z" stroke="#EDE246" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M13.5975 9.22283C13.5975 8.6854 13.4239 8.25833 13.0768 7.94167C12.7297 7.625 12.2699 7.46667 11.6975 7.46667C11.3441 7.46667 11.0242 7.5446 10.7378 7.7005C10.4515 7.8564 10.2047 8.084 9.99749 8.38333C9.87526 8.5611 9.71139 8.67223 9.50582 8.71667C9.30026 8.7611 9.10306 8.73333 8.91416 8.63333C8.70306 8.5111 8.57526 8.3611 8.53082 8.18333C8.48639 8.00557 8.53082 7.8111 8.66416 7.6C8.99749 7.08889 9.42872 6.69444 9.95782 6.41667C10.4869 6.13889 11.0668 6 11.6975 6C12.7419 6 13.5808 6.29022 14.2142 6.87067C14.8475 7.451 15.1642 8.21077 15.1642 9.15C15.1642 9.6611 15.0531 10.1333 14.8308 10.5667C14.6086 11 14.2419 11.4667 13.7308 11.9667C13.3197 12.3556 13.0419 12.6651 12.8975 12.8953C12.7531 13.1256 12.6586 13.3882 12.6142 13.6833C12.5808 13.9167 12.4808 14.1111 12.3142 14.2667C12.1475 14.4222 11.9542 14.5 11.7342 14.5C11.5143 14.5 11.3254 14.425 11.1675 14.275C11.0097 14.125 10.9308 13.95 10.9308 13.75C10.9308 13.3722 11.0308 13.0056 11.2308 12.65C11.4308 12.2944 11.7384 11.9266 12.1535 11.5463C12.6828 11.071 13.0558 10.6556 13.2725 10.3C13.4892 9.94443 13.5975 9.5854 13.5975 9.22283ZM11.696 18.6667C11.3748 18.6667 11.1003 18.5523 10.8725 18.3235C10.6447 18.0947 10.5308 17.8197 10.5308 17.4985C10.5308 17.1773 10.6452 16.9028 10.874 16.675C11.1028 16.4472 11.3778 16.3333 11.699 16.3333C12.0202 16.3333 12.2947 16.4477 12.5225 16.6765C12.7503 16.9053 12.8642 17.1803 12.8642 17.5015C12.8642 17.8227 12.7498 18.0972 12.521 18.325C12.2922 18.5528 12.0172 18.6667 11.696 18.6667Z" fill="#EDE246"/>
        </g>
        <defs>
        <clipPath id="${clipId}">
        <rect width="24" height="24" fill="white"/>
        </clipPath>
        </defs>
        </svg>`;
        badge.innerHTML = svgIcon;
      } else if (level === "loading") {
        const spinnerId = `trustlens-spinner-${id.replace(
          /[^a-zA-Z0-9]/g,
          "-"
        )}`;
        const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle;">
         <circle cx="12" cy="12" r="10" stroke="#ccc" stroke-width="2" fill="none" opacity="0.3"/>
         <circle cx="12" cy="12" r="10" stroke="#666" stroke-width="2" fill="none" stroke-dasharray="31.416" stroke-dashoffset="31.416" opacity="0.7">
           <animate attributeName="stroke-dashoffset" dur="1s" values="31.416;0" repeatCount="indefinite"/>
           <animateTransform attributeName="transform" type="rotate" dur="1s" values="0 12 12;360 12 12" repeatCount="indefinite"/>
         </circle>
       </svg>`;
        badge.innerHTML = svgIcon;
      } else {
        badge.innerHTML = "";
      }

      badge.style.display = "inline-flex";
      badge.style.alignItems = "center";
      badge.style.justifyContent = "center";
      badge.style.fontSize = "11px";
      badge.style.padding = "0";
      badge.style.borderRadius = "0";
      badge.style.border = "none";
      badge.style.fontWeight = "600";
      badge.style.verticalAlign = "middle";
      badge.style.width = "auto";
      badge.style.height = "auto";
      badge.style.minWidth = "auto";
      badge.style.minHeight = "auto";
      badge.style.boxSizing = "border-box";
      badge.style.flexShrink = "0";
      badge.style.background = "transparent";
      badge.style.color = "inherit";

      if (level !== "loading") {
        this.addHoverListeners(badge, level, badgeColor, badgeData);
      }

      const commentRoot =
        el.closest("shreddit-comment") ||
        el.closest('article[data-testid="comment"]') ||
        el.closest(this.ROOT_SELECTOR) ||
        el;
      console.log(
        "TrustLens: Comment root:",
        commentRoot.tagName,
        commentRoot.getAttribute("data-testid") || commentRoot.className
      );

      const usernameSelectors = [
        'a[href^="/user/"]',
        'a[href^="/u/"]',
        'a[data-testid="comment_author_link"]',
        ".author",
      ];

      let usernameEl = null;
      for (const sel of usernameSelectors) {
        const found = commentRoot.querySelector(sel);
        if (found) {
          console.log(
            "TrustLens: Found username with selector:",
            sel,
            "Username:",
            found.textContent
          );
          usernameEl = found;
          break;
        }
      }

      if (!usernameEl) {
        console.log("TrustLens: No username found, using fallback");
      }

      if (usernameEl && usernameEl.parentElement) {
        console.log(
          "TrustLens: Found username element:",
          usernameEl.textContent
        );

        let metadataRow = null;
        let current = usernameEl;
        let depth = 0;

        while (current && depth < 10) {
          const classList = current.classList
            ? Array.from(current.classList).join(" ")
            : "no-classes";
          console.log(
            `TrustLens: Level ${depth}: ${current.tagName} classes="${classList}"`
          );

          if (
            current.classList &&
            current.classList.contains("flex") &&
            current.classList.contains("flex-none") &&
            current.classList.contains("flex-row") &&
            current.classList.contains("flex-nowrap") &&
            current.classList.contains("items-center")
          ) {
            console.log(
              "TrustLens: Found THE CORRECT flex-none flex-nowrap flex-row items-center container!"
            );
            metadataRow = current;
            break;
          }

          current = current.parentElement;
          depth++;
        }

        if (!metadataRow) {
          console.warn(
            "TrustLens: Could not find the correct metadata row, trying flex flex-row items-center"
          );
          current = usernameEl;
          depth = 0;

          while (current && depth < 10) {
            if (
              current.classList &&
              current.classList.contains("flex") &&
              current.classList.contains("flex-row") &&
              current.classList.contains("items-center")
            ) {
              console.log(
                "TrustLens: Found flex flex-row items-center container!"
              );
              metadataRow = current;
              break;
            }
            current = current.parentElement;
            depth++;
          }
        }

        if (!metadataRow) {
          console.warn("TrustLens: Could not find metadata row");
          current = usernameEl;
          depth = 0;
          while (current && depth < 10) {
            if (current.querySelector && current.querySelector("time")) {
              console.log(
                "TrustLens: Using fallback - found container with time at depth",
                depth
              );
              metadataRow = current;
              break;
            }
            current = current.parentElement;
            depth++;
          }
        }

        if (!metadataRow) {
          console.error(
            "TrustLens: Could not find any suitable container for badge"
          );
        } else {
          console.log(
            "TrustLens: Final container:",
            metadataRow.className,
            metadataRow.tagName
          );

          const isInsideCommentMeta = metadataRow.closest(
            '[slot="commentMeta"]'
          );
          console.log("TrustLens: Inside commentMeta?", !!isInsideCommentMeta);

          badge.classList.add("trustlens-inline");

          const commentMeta = commentRoot.querySelector('[slot="commentMeta"]');
          if (commentMeta) {
            commentMeta.querySelectorAll(".trustlens-badge").forEach((b) => {
              console.log(
                "TrustLens: Removing existing badge from commentMeta"
              );
              b.remove();
            });

            commentMeta.style.display = "flex";
            commentMeta.style.justifyContent = "space-between";
            commentMeta.style.alignItems = "center";
            commentMeta.style.width = "100%";

            commentMeta.appendChild(badge);
            console.log(
              "TrustLens: Badge appended to commentMeta with justify-between"
            );
          } else {
            const summary = commentRoot.querySelector("summary");
            if (summary) {
              summary
                .querySelectorAll(".trustlens-badge")
                .forEach((b) => b.remove());
              summary.style.display = "flex";
              summary.style.justifyContent = "space-between";
              summary.style.alignItems = "center";
              summary.style.width = "100%";
              summary.appendChild(badge);
              console.log(
                "TrustLens: Badge appended to summary with justify-between (fallback)"
              );
            } else {
              metadataRow.querySelectorAll(".trustlens-badge").forEach((b) => {
                console.log("TrustLens: Removing existing badge from metadata");
                b.remove();
              });
              metadataRow.appendChild(badge);
            }
          }

          console.log(
            "TrustLens: Badge inserted successfully!",
            "Badge:",
            badge.textContent
          );
          return;
        }
      }

      console.log("TrustLens: Using fallback insertion method");
      let targetContainer = null;
      const md = el.querySelector(".md");
      if (
        md &&
        (md.parentElement === el || md.closest(this.ROOT_SELECTOR) === el)
      ) {
        targetContainer = md;
      }
      if (!targetContainer) {
        const usertext = el.querySelector(".usertext-body");
        if (
          usertext &&
          (usertext.parentElement === el ||
            usertext.closest(this.ROOT_SELECTOR) === el)
        ) {
          targetContainer = usertext;
        }
      }
      if (!targetContainer) targetContainer = el;

      targetContainer
        .querySelectorAll(".trustlens-badge")
        .forEach((b) => b.remove());
      targetContainer.insertAdjacentElement("afterbegin", badge);
      console.log("TrustLens: Fallback badge inserted");
    }
  }

  window.trustLensDuplicateProof = new DuplicateProofManager();
})();
