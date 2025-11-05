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
       .trustlens-badge.trustlens-inline{width:auto !important;height:auto !important;padding:3px 8px !important;border-radius:10px !important;border:1px solid rgba(0,0,0,.12) !important;margin-right:8px;vertical-align:middle;line-height:1;font-size:11px !important;}
       .trustlens-user-row{display:flex;align-items:center;justify-content:space-between;gap:8px}
       .trustlens-safe{background:#d4edda;color:#155724}
       .trustlens-low{background:#fff3cd;color:#856404}
       .trustlens-medium{background:#f8d7da;color:#721c24}
       .trustlens-high{background:#d1ecf1;color:#0c5460}
       .trustlens-severe{background:#f5c6cb;color:#721c24}
       .trustlens-toxic{background:#dc3545;color:#fff}
       .trustlens-mild{background:#ffc107;color:#000}
       .trustlens-neutral{background:#28a745;color:#fff}
       .trustlens-loading{background:#f8f9fa;color:#6c757d}
      
       .trustlens-popup {
         position: absolute;
         z-index: 10000;
         background: white;
         border: 1px solid #e0e0e0;
         border-radius: 8px;
         padding: 10px 25px 10px 25px;
         box-shadow: 0 4px 12px rgba(0,0,0,0.15);
         min-width: 300px;
         max-width: 374px;
         font-family: system-ui, -apple-system, sans-serif;
         font-size: 13px;
         line-height: 1.5;
         color: #333;
         display: none;
         pointer-events: auto;
         margin-top: 8px;
       }
      
       .trustlens-popup.show {
         display: block;
       }
      
       .trustlens-popup-title {
         font-weight: 600;
         font-size: 14px;
         margin-bottom: 12px;
         color: #1a1a1a;
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
         color: #0066cc;
         text-decoration: none;
         font-weight: 500;
         margin-top: 8px;
         display: inline-block;
         cursor: pointer;
       }
      
       .trustlens-popup-link:hover {
         text-decoration: underline;
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
     const overlay = document.createElement('div');
     overlay.className = 'trustlens-sidebar-overlay';
     overlay.id = 'trustlens-sidebar-overlay';
     overlay.addEventListener('click', () => this.closeSidebar());
     document.body.appendChild(overlay);


     // Create sidebar
     const sidebar = document.createElement('div');
     sidebar.className = 'trustlens-sidebar';
     sidebar.id = 'trustlens-sidebar';
    
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
    
     document.getElementById('trustlens-sidebar-close').addEventListener('click', () => this.closeSidebar());
   }


   openSidebar(level, badgeColor) {
     const sidebar = document.getElementById('trustlens-sidebar');
     const overlay = document.getElementById('trustlens-sidebar-overlay');
     const content = document.getElementById('trustlens-sidebar-content');
    
     // Populate sidebar content based on level
     content.innerHTML = this.getSidebarContent(level, badgeColor);
    
     // Show sidebar
     overlay.classList.add('show');
     sidebar.classList.add('open');
   }


   closeSidebar() {
     const sidebar = document.getElementById('trustlens-sidebar');
     const overlay = document.getElementById('trustlens-sidebar-overlay');
    
     overlay.classList.remove('show');
     sidebar.classList.remove('open');
   }


   getSidebarContent(level, badgeColor) {
     // Define metrics based on badge type
     const metrics = {
       neutral: {
         tone: 90,
         toxicity: 5,
         hostility: 3,
         credibility: 75
       },
       mild: {
         tone: 60,
         toxicity: 25,
         hostility: 15,
         credibility: 45
       },
       toxic: {
         tone: 20,
         toxicity: 85,
         hostility: 75,
         credibility: 15
       }
     };


     const tags = {
       neutral: ['personal tone', 'qualified claims', 'personal experience noted', 'no loaded language'],
       mild: ['subjective tone', 'opinion-based', 'limited sources', 'personal viewpoint'],
       toxic: ['hostile language', 'unverified claims', 'emotional language', 'loaded terms']
     };


     const currentMetrics = metrics[level] || metrics.neutral;
     const currentTags = tags[level] || tags.neutral;


     return `
       <a href="#" class="trustlens-sidebar-link">Why am I seeing this?</a>
      
       <div class="trustlens-sidebar-section">
         <div class="trustlens-sidebar-section-title">Analysis Breakdown</div>
        
         <div class="trustlens-metric">
           <div class="trustlens-metric-header">
             <span class="trustlens-metric-label">Tone</span>
             <span class="trustlens-metric-value">${currentMetrics.tone}%</span>
           </div>
           <div class="trustlens-metric-bar">
             <div class="trustlens-metric-fill tone" style="width: ${currentMetrics.tone}%"></div>
           </div>
         </div>
        
         <div class="trustlens-metric">
           <div class="trustlens-metric-header">
             <span class="trustlens-metric-label">Toxicity</span>
             <span class="trustlens-metric-value">${currentMetrics.toxicity}%</span>
           </div>
           <div class="trustlens-metric-bar">
             <div class="trustlens-metric-fill toxicity" style="width: ${currentMetrics.toxicity}%"></div>
           </div>
         </div>
        
         <div class="trustlens-metric">
           <div class="trustlens-metric-header">
             <span class="trustlens-metric-label">Hostility</span>
             <span class="trustlens-metric-value">${currentMetrics.hostility}%</span>
           </div>
           <div class="trustlens-metric-bar">
             <div class="trustlens-metric-fill hostility" style="width: ${currentMetrics.hostility}%"></div>
           </div>
         </div>
        
         <div class="trustlens-metric">
           <div class="trustlens-metric-header">
             <span class="trustlens-metric-label">Credibility</span>
             <span class="trustlens-metric-value">${currentMetrics.credibility}%</span>
           </div>
           <div class="trustlens-metric-bar">
             <div class="trustlens-metric-fill credibility" style="width: ${currentMetrics.credibility}%"></div>
           </div>
         </div>
       </div>
      
       <div class="trustlens-sidebar-section">
         <div class="trustlens-sidebar-section-title">Signals Scan</div>
         <div class="trustlens-tags">
           ${currentTags.map(tag => `<span class="trustlens-tag">${tag}</span>`).join('')}
         </div>
       </div>
      
       <div class="trustlens-sidebar-section">
         <div class="trustlens-sidebar-section-title">Color Indicators</div>
         <div class="trustlens-color-legend">
           <div class="trustlens-color-item">
             <div class="trustlens-color-dot green"></div>
             <div class="trustlens-color-text">
               <div class="trustlens-color-title">Green - Balanced</div>
               <div class="trustlens-color-desc">High credibility content with neutral tone, factual statements, and cited sources.</div>
             </div>
           </div>
           <div class="trustlens-color-item">
             <div class="trustlens-color-dot yellow"></div>
             <div class="trustlens-color-text">
               <div class="trustlens-color-title">Yellow - Opinion/Unverified</div>
               <div class="trustlens-color-desc">Medium credibility with some subjective statements or uncited sources.</div>
             </div>
           </div>
           <div class="trustlens-color-item">
             <div class="trustlens-color-dot red"></div>
             <div class="trustlens-color-text">
               <div class="trustlens-color-title">Red - Hostile/Low Evidence</div>
               <div class="trustlens-color-desc">Low credibility with emotional language, unsubstantiated claims, or toxic markers.</div>
             </div>
           </div>
         </div>
       </div>
      
       <div class="trustlens-sidebar-section">
         <div class="trustlens-sidebar-section-title">Referenced Sites</div>
         <a href="#" class="trustlens-sidebar-link">None</a>
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
       if (n && n.textContent && n.textContent.trim().length > 10)
         return n.textContent.trim();
     }
     const all = el.textContent.trim();
     return all.length > 10 ? all : null;
   }


   async testAPI() {
     try {
       const r = await fetch(`${API_BASE}/health`);
       this.update("tl-api", r.ok ? "Connected" : "Error");
     } catch {
       this.update("tl-api", "Failed");
     }
   }


   getPopupContent(level, badgeColor) {
     const content = {
       neutral: {
         title: "Uses a neutral tone and mentions verifiable evidence.",
         sections: [
           { label: "Tone:", value: "Low toxicity, no hostility detected." },
           { label: "Evidence:", value: "Evidence present and verified." },
           { label: "Source:", value: "Includes verified sources." }
         ]
       },
       toxic: {
         title: "This content shows signs of hostility and emotional language.",
         sections: [
           { label: "Tone:", value: "Hostile tone detected." },
           { label: "Evidence:", value: "Evidence unverified or absent." },
           { label: "Source:", value: "Source authenticity unclear." },
           { label: "Emotion:", value: "Emotionally-charged." }
         ]
       },
       mild: {
         title: "Includes subjective language and personal viewpoints.",
         sections: [
           { label: "Tone:", value: "Neutral to slightly subjective tone." },
           { label: "Emotion:", value: "Reflects personal perspective." },
           { label: "Evidence:", value: "Limited or no evidence cited." },
           { label: "Source:", value: "No credible sources detected." }
         ]
       }
     };


     return content[level] || content.neutral;
   }


   createPopup(badge, level, badgeColor) {
     document.querySelectorAll('.trustlens-popup').forEach(p => p.remove());


     const popup = document.createElement('div');
     popup.className = 'trustlens-popup';
    
     const popupData = this.getPopupContent(level, badgeColor);
    
     let sectionsHTML = '';
     popupData.sections.forEach(section => {
       sectionsHTML += `
         <div class="trustlens-popup-section">
           <div class="trustlens-popup-label">${section.label}</div>
           <div class="trustlens-popup-value">${section.value}</div>
         </div>
       `;
     });


     popup.innerHTML = `
       <div class="trustlens-popup-title">${popupData.title}</div>
       ${sectionsHTML}
       <a href="#" class="trustlens-popup-link" data-level="${level}" data-color="${badgeColor}">Learn more</a>
     `;


     document.body.appendChild(popup);
    
     const badgeRect = badge.getBoundingClientRect();
     popup.style.left = `${badgeRect.left}px`;
     popup.style.top = `${badgeRect.bottom + window.scrollY}px`;
    
     // Add click event to "Learn more" link
     const learnMoreLink = popup.querySelector('.trustlens-popup-link');
     learnMoreLink.addEventListener('click', (e) => {
       e.preventDefault();
       e.stopPropagation();
       this.openSidebar(level, badgeColor);
       popup.remove();
     });
    
     return popup;
   }


   addHoverListeners(badge, level, badgeColor) {
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
           popup.classList.remove('show');
           setTimeout(() => {
             if (popup && popup.parentElement) {
               popup.remove();
             }
             popup = null;
           }, 200);
         }
       }, 300);
     };


     badge.addEventListener('mouseenter', () => {
       clearHideTimeout();
      
       popup = this.createPopup(badge, level, badgeColor);
      
       // Add hover listeners to the popup itself
       popup.addEventListener('mouseenter', () => {
         clearHideTimeout();
       });
      
       popup.addEventListener('mouseleave', () => {
         scheduleHide();
       });
      
       // Small delay before showing
       setTimeout(() => {
         if (popup) {
           popup.classList.add('show');
         }
       }, 100);
     });


     badge.addEventListener('mouseleave', () => {
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
       const res = await fetch(`${API_BASE}/predict`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ texts: [text] }),
       });
       if (!res.ok) throw new Error(`HTTP ${res.status}`);
       const data = await res.json();


       console.log("TrustLens: API response keys:", Object.keys(data));
       console.log(
         "TrustLens: badge_colors in response:",
         "badge_colors" in data
       );
       console.log("TrustLens: badge_colors value:", data.badge_colors);


       const badgeColor =
         data.badge_colors && data.badge_colors[0]
           ? data.badge_colors[0]
           : "green";


       console.log("TrustLens: Selected badgeColor:", badgeColor);


       const colorToLabel = {
         red: "Toxic",
         yellow: "Mild",
         green: "Neutral",
       };


       const displayText = colorToLabel[badgeColor] || "Neutral";
       const levelKey =
         badgeColor === "red"
           ? "toxic"
           : badgeColor === "yellow"
           ? "mild"
           : "neutral";


       this.insertBadge(el, id, levelKey, displayText, true, badgeColor);
       this.processedCommentIds.add(id);
     } catch (e) {
       console.warn("TrustLens: analysis failed", e);
       this.insertBadge(el, id, "toxic", "Error");
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


   insertBadge(el, id, level, text, replace = false, badgeColor = null) {
     console.log("TrustLens: insertBadge called", {
       id,
       level,
       text,
       replace,
       badgeColor
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
       toxic: "Toxic",
       mild: "Mild",
       neutral: "Neutral",
       safe: "Balanced",
       warning: "Scope for checks",
       dangerous: "Potential Fraud",
       loading: "Analyzing...",
     };


     const displayText = labelMap[level] || text;


     const badge = document.createElement("span");
     badge.className = `trustlens-badge trustlens-${level}`;
     badge.dataset.commentId = id;


     if (level === "neutral") {
       const clipId = `trustlens-neutral-clip-${id.replace(
         /[^a-zA-Z0-9]/g,
         "-"
       )}`;
       const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
         <g clip-path="url(#${clipId})">
           <path d="M22.5714 9.25487V6.14286C22.5714 5.19609 21.8039 4.42857 20.8571 4.42857H18.9767C17.4197 4.42857 15.909 3.89865 14.6932 2.92595L12.2857 1L9.87827 2.92597C8.6624 3.89865 7.1517 4.42857 5.59465 4.42857H3.71429C2.76752 4.42857 2 5.19609 2 6.14286V9.25487C2 15.4859 6.24073 20.9173 12.2857 22.4286C18.3306 20.9173 22.5714 15.4859 22.5714 9.25487Z" stroke="currentColor" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M15.7123 8.017C15.8884 7.85335 16.1227 7.76288 16.3659 7.76467C16.609 7.76647 16.8419 7.86039 17.0154 8.02662C17.1889 8.19285 17.2895 8.41839 17.2959 8.65564C17.3024 8.89289 17.2141 9.1233 17.0498 9.29825L12.0623 15.3872C11.9766 15.4774 11.8731 15.5498 11.758 15.6C11.6429 15.6502 11.5187 15.6773 11.3926 15.6796C11.2666 15.6819 11.1414 15.6593 11.0245 15.6133C10.9076 15.5672 10.8015 15.4987 10.7123 15.4116L7.40483 12.1829C7.31272 12.0991 7.23884 11.9981 7.1876 11.8858C7.13636 11.7735 7.10881 11.6524 7.10659 11.5295C7.10437 11.4066 7.12753 11.2845 7.17468 11.1706C7.22183 11.0566 7.29201 10.9531 7.38103 10.8662C7.47006 10.7793 7.5761 10.7108 7.69283 10.6648C7.80957 10.6187 7.93461 10.5961 8.06048 10.5983C8.18636 10.6005 8.3105 10.6274 8.4255 10.6774C8.5405 10.7274 8.644 10.7995 8.72983 10.8894L11.3473 13.4434L15.6886 8.04384L15.7123 8.017Z" fill="currentColor"/>
         </g>
         <defs>
           <clipPath id="${clipId}">
             <rect width="24" height="23.4286" fill="white"/>
           </clipPath>
         </defs>
       </svg>`;
       badge.innerHTML = svgIcon + displayText;
     } else if (level === "toxic") {
       const clipId = `trustlens-toxic-clip-${id.replace(
         /[^a-zA-Z0-9]/g,
         "-"
       )}`;
       const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none">
<g clip-path="url(#clip0_265_155)">
<path d="M22.5714 9.25487V6.14286C22.5714 5.19609 21.8039 4.42857 20.8571 4.42857H18.9767C17.4197 4.42857 15.909 3.89865 14.6932 2.92595L12.2857 1L9.87827 2.92597C8.6624 3.89865 7.1517 4.42857 5.59465 4.42857H3.71429C2.76752 4.42857 2 5.19609 2 6.14286V9.25487C2 15.4859 6.24073 20.9173 12.2857 22.4286C18.3306 20.9173 22.5714 15.4859 22.5714 9.25487Z" stroke="#FDFBFB" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
<g clip-path="url(#clip1_265_155)">
<path d="M12.0002 12.5894L9.27787 15.3186C9.15191 15.4436 9.00491 15.5061 8.83683 15.5061C8.66879 15.5061 8.52183 15.4436 8.396 15.3186C8.271 15.1936 8.2085 15.0478 8.2085 14.8811C8.2085 14.7144 8.271 14.5686 8.396 14.4436L11.1252 11.7144L8.396 9.01298C8.271 8.88702 8.2085 8.73998 8.2085 8.57194C8.2085 8.4039 8.271 8.25694 8.396 8.1311C8.521 8.0061 8.66683 7.9436 8.8335 7.9436C9.00016 7.9436 9.146 8.0061 9.271 8.1311L12.0002 10.8603L14.7016 8.1311C14.8137 8.0061 14.9572 7.9436 15.1322 7.9436C15.3072 7.9436 15.4577 8.0061 15.5835 8.1311C15.7085 8.2561 15.771 8.40194 15.771 8.5686C15.771 8.73527 15.7085 8.8811 15.5835 9.0061L12.8543 11.7144L15.5835 14.4367C15.7085 14.5627 15.771 14.7097 15.771 14.8778C15.771 15.0458 15.7085 15.1928 15.5835 15.3186C15.4585 15.4436 15.3127 15.5061 15.146 15.5061C14.9793 15.5061 14.8335 15.4436 14.7085 15.3186L12.0002 12.5894Z" fill="#FDFBFB"/>
</g>
</g>
<defs>
<clipPath id="clip0_265_155">
<rect width="24" height="23.4286" fill="white"/>
</clipPath>
<clipPath id="clip1_265_155">
<rect width="20" height="20" fill="white" transform="translate(2 1.71436)"/>
</clipPath>
</defs>
       </svg>`;
       badge.innerHTML = svgIcon + displayText;
     } else if (level === 'mild') {
       const clipId = `trustlens-mild-clip-${id.replace(/[^a-zA-Z0-9]/g, '-')}`;
       const svgIcon = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" style="display: inline-block; vertical-align: middle; margin-right: 4px;">
         <g clip-path="url(#${clipId})">
           <path d="M22.2858 9.54051V6.4285C22.2858 5.48174 21.5183 4.71422 20.5715 4.71422H18.6911C17.1341 4.71422 15.6234 4.1843 14.4075 3.21159L12.0001 1.28564L9.59263 3.21161C8.37676 4.1843 6.86606 4.71422 5.30901 4.71422H3.42864C2.48188 4.71422 1.71436 5.48174 1.71436 6.4285V9.54051C1.71436 15.7715 5.95509 21.2029 12.0001 22.7142C18.045 21.2029 22.2858 15.7715 22.2858 9.54051Z" stroke="currentColor" stroke-width="2.14286" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M13.5975 9.22283C13.5975 8.6854 13.4239 8.25833 13.0768 7.94167C12.7297 7.625 12.2699 7.46667 11.6975 7.46667C11.3441 7.46667 11.0242 7.5446 10.7378 7.7005C10.4515 7.8564 10.2047 8.084 9.99749 8.38333C9.87526 8.5611 9.71139 8.67223 9.50582 8.71667C9.30026 8.7611 9.10306 8.73333 8.91416 8.63333C8.70306 8.5111 8.57526 8.3611 8.53082 8.18333C8.48639 8.00557 8.53082 7.8111 8.66416 7.6C8.99749 7.08889 9.42872 6.69444 9.95782 6.41667C10.4869 6.13889 11.0668 6 11.6975 6C12.7419 6 13.5808 6.29022 14.2142 6.87067C14.8475 7.451 15.1642 8.21077 15.1642 9.15C15.1642 9.6611 15.0531 10.1333 14.8308 10.5667C14.6086 11 14.2419 11.4667 13.7308 11.9667C13.3197 12.3556 13.0419 12.6651 12.8975 12.8953C12.7531 13.1256 12.6586 13.3882 12.6142 13.6833C12.5808 13.9167 12.4808 14.1111 12.3142 14.2667C12.1475 14.4222 11.9542 14.5 11.7342 14.5C11.5143 14.5 11.3254 14.425 11.1675 14.275C11.0097 14.125 10.9308 13.95 10.9308 13.75C10.9308 13.3722 11.0308 13.0056 11.2308 12.65C11.4308 12.2944 11.7384 11.9266 12.1535 11.5463C12.6828 11.071 13.0558 10.6556 13.2725 10.3C13.4892 9.94443 13.5975 9.5854 13.5975 9.22283ZM11.696 18.6667C11.3748 18.6667 11.1003 18.5523 10.8725 18.3235C10.6447 18.0947 10.5308 17.8197 10.5308 17.4985C10.5308 17.1773 10.6452 16.9028 10.874 16.675C11.1028 16.4472 11.3778 16.3333 11.699 16.3333C12.0202 16.3333 12.2947 16.4477 12.5225 16.6765C12.7503 16.9053 12.8642 17.1803 12.8642 17.5015C12.8642 17.8227 12.7498 18.0972 12.521 18.325C12.2922 18.5528 12.0172 18.6667 11.696 18.6667Z" fill="currentColor"/>
         </g>
         <defs>
           <clipPath id="${clipId}">
             <rect width="24" height="24" fill="white"/>
           </clipPath>
         </defs>
       </svg>`;
       badge.innerHTML = svgIcon + displayText;
     } else {
       badge.textContent = displayText;
     }


     badge.style.display = "inline-flex";
     badge.style.alignItems = "center";
     badge.style.fontSize = "11px";
     badge.style.padding = "4px 12px";
     badge.style.borderRadius = "12px";
     badge.style.border = "none";
     badge.style.fontWeight = "600";
     badge.style.verticalAlign = "middle";
     badge.style.width = "auto";
     badge.style.height = "auto";
     badge.style.boxSizing = "border-box";
     badge.style.flexShrink = "0";
     badge.style.justifyContent = "space-between";


     switch (level) {
       case "toxic":
         badge.style.background = "#D32F2F";
         badge.style.color = "white";
         break;
       case "mild":
         badge.style.background = "#EDE246";
         badge.style.color = "#000";
         break;
       case "neutral":
         badge.style.background = "#388E3C";
         badge.style.color = "white";
         break;
       default:
         badge.style.background = "#1976d2";
         badge.style.color = "white";
     }


     if (level !== 'loading') {
       this.addHoverListeners(badge, level, badgeColor);
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
             console.log("TrustLens: Removing existing badge from commentMeta");
             b.remove();
           });
          
           commentMeta.style.display = 'flex';
           commentMeta.style.justifyContent = 'space-between';
           commentMeta.style.alignItems = 'center';
           commentMeta.style.width = '100%';
          
           commentMeta.appendChild(badge);
           console.log("TrustLens: Badge appended to commentMeta with justify-between");
         } else {
           const summary = commentRoot.querySelector('summary');
           if (summary) {
             summary.querySelectorAll(".trustlens-badge").forEach((b) => b.remove());
             summary.style.display = 'flex';
             summary.style.justifyContent = 'space-between';
             summary.style.alignItems = 'center';
             summary.style.width = '100%';
             summary.appendChild(badge);
             console.log("TrustLens: Badge appended to summary with justify-between (fallback)");
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

