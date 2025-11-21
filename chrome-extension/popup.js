// TrustLens Popup Interface
document.addEventListener('DOMContentLoaded', () => {
    initializePopup();
});

function initializePopup() {
    // Create the popup HTML
    document.body.innerHTML = `
        <div style="width: 300px; padding: 16px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <div style="text-align: center; margin-bottom: 16px;">
                <h2 style="margin: 0; color: #333; font-size: 18px;">🛡️ TrustLens</h2>
            </div>
            
            <div id="status-section" style="margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <div id="status-indicator" style="width: 8px; height: 8px; border-radius: 50%; background: #28a745;"></div>
                    <span id="status-text" style="font-size: 14px; color: #333;">Active</span>
                </div>
                <div id="stats" style="font-size: 12px; color: #666;">
                    <div>Comments analyzed: <span id="analyzed-count">0</span></div>
                    <div>Toxic comments: <span id="toxic-count">0</span></div>
                </div>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 8px; font-size: 14px; color: #333;">
                    <input type="checkbox" id="enable-badges" checked style="margin-right: 8px;">
                    Show toxicity badges
                </label>
                <label style="display: block; margin-bottom: 8px; font-size: 14px; color: #333;">
                    <input type="checkbox" id="enable-tooltips" checked style="margin-right: 8px;">
                    Show detailed tooltips
                </label>
            </div>
            
            <div style="margin-bottom: 16px;">
                <label style="display: block; margin-bottom: 4px; font-size: 14px; color: #333;">
                    Sensitivity: <span id="sensitivity-value">0.5</span>
                </label>
                <input type="range" id="sensitivity-slider" min="0.1" max="1" step="0.1" value="0.5" 
                       style="width: 100%; margin-bottom: 8px;">
            </div>
            
            <div style="display: flex; gap: 8px; margin-bottom: 16px;">
                <button id="analyze-current" style="flex: 1; padding: 8px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Analyze Current Page
                </button>
                <button id="export-data" style="flex: 1; padding: 8px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Export Data
                </button>
            </div>
            
            <div id="recent-analysis" style="margin-top: 16px;">
                <h4 style="margin: 0 0 8px 0; font-size: 14px; color: #333;">Recent Analysis</h4>
                <div id="analysis-list" style="max-height: 150px; overflow-y: auto; font-size: 12px;">
                    <div style="color: #666; text-align: center; padding: 8px;">No recent analysis</div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners
    setupEventListeners();
    loadSettings();
    updateStatus();
}

function setupEventListeners() {
    document.getElementById('enable-badges').addEventListener('change', (e) => {
        chrome.storage.local.set({ 'trustlens-badges-enabled': e.target.checked });
        sendMessageToTab({ type: 'TOGGLE_BADGES', enabled: e.target.checked });
    });
    
    document.getElementById('enable-tooltips').addEventListener('change', (e) => {
        chrome.storage.local.set({ 'trustlens-tooltips-enabled': e.target.checked });
        sendMessageToTab({ type: 'TOGGLE_TOOLTIPS', enabled: e.target.checked });
    });
    
    document.getElementById('sensitivity-slider').addEventListener('input', (e) => {
        const value = parseFloat(e.target.value);
        document.getElementById('sensitivity-value').textContent = value;
        chrome.storage.local.set({ 'trustlens-sensitivity': value });
        sendMessageToTab({ type: 'UPDATE_SENSITIVITY', threshold: value });
    });
    
    document.getElementById('analyze-current').addEventListener('click', () => {
        sendMessageToTab({ type: 'ANALYZE_CURRENT_PAGE' });
    });
    
    document.getElementById('export-data').addEventListener('click', () => {
        exportAnalysisData();
    });
}

function loadSettings() {
    chrome.storage.local.get([
        'trustlens-badges-enabled',
        'trustlens-tooltips-enabled', 
        'trustlens-sensitivity'
    ], (result) => {
        document.getElementById('enable-badges').checked = result['trustlens-badges-enabled'] !== false;
        document.getElementById('enable-tooltips').checked = result['trustlens-tooltips-enabled'] !== false;
        const sensitivity = result['trustlens-sensitivity'] || 0.5;
        document.getElementById('sensitivity-slider').value = sensitivity;
        document.getElementById('sensitivity-value').textContent = sensitivity;
    });
}

function updateStatus() {
    chrome.storage.local.get(['trustlens-stats'], (result) => {
        const stats = result['trustlens-stats'] || { analyzed: 0, toxic: 0 };
        document.getElementById('analyzed-count').textContent = stats.analyzed;
        document.getElementById('toxic-count').textContent = stats.toxic;
        
        // Update status indicator
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (stats.analyzed > 0) {
            indicator.style.background = '#28a745';
            statusText.textContent = 'Active';
        } else {
            indicator.style.background = '#ffc107';
            statusText.textContent = 'Ready';
        }
    });
}

function sendMessageToTab(message) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
            chrome.tabs.sendMessage(tabs[0].id, message);
        }
    });
}

function exportAnalysisData() {
    chrome.storage.local.get(['trustlens-analysis-history'], (result) => {
        const history = result['trustlens-analysis-history'] || [];
        const dataStr = JSON.stringify(history, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `trustlens-analysis-${new Date().toISOString().split('T')[0]}.json`;
        link.click();
        
        URL.revokeObjectURL(url);
    });
}

// Listen for updates from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'ANALYSIS_UPDATE') {
        updateStatus();
        updateAnalysisList(message.data);
    }
});

function updateAnalysisList(data) {
    const list = document.getElementById('analysis-list');
    if (data && data.length > 0) {
        list.innerHTML = data.slice(-5).map(item => `
            <div style="padding: 4px 0; border-bottom: 1px solid #eee;">
                <div style="font-weight: 500;">${item.level}</div>
                <div style="color: #666;">${item.text.substring(0, 50)}...</div>
            </div>
        `).join('');
    }
}