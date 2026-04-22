// Popup render logic, extracted as a pure function so the DOM rendering
// can be verified by jsdom tests without launching the extension.
// Consumes a TrustCalculateResponse (or an error reply) and mutates the
// provided root element.

function renderTrustResult(root, response) {
  if (!root) {
    throw new Error('renderTrustResult: root element is required');
  }

  // Clear previous contents so repeat renders stay consistent.
  root.innerHTML = '';

  if (!response || response.error) {
    const err = document.createElement('div');
    err.className = 'trustlens-error';
    err.setAttribute('data-testid', 'trust-error');
    err.textContent = errorMessage(response);
    root.appendChild(err);
    return;
  }

  const badge = document.createElement('div');
  badge.className = 'trustlens-badge';
  badge.setAttribute('data-testid', 'trust-badge');
  badge.style.backgroundColor = response.color || '#999999';

  const label = document.createElement('span');
  label.className = 'trustlens-badge-label';
  label.setAttribute('data-testid', 'trust-badge-label');
  label.textContent = response.label || 'Unknown';
  badge.appendChild(label);

  if (typeof response.score === 'number') {
    const score = document.createElement('span');
    score.className = 'trustlens-badge-score';
    score.setAttribute('data-testid', 'trust-badge-score');
    score.textContent = String(Math.round(response.score));
    badge.appendChild(score);
  }

  root.appendChild(badge);
}

function errorMessage(response) {
  if (!response) return 'Unable to calculate trust';
  switch (response.error) {
    case 'NETWORK':
      return 'Network error — is the TrustLens backend running?';
    case 'SERVER':
      return `Server error (${response.status || 'unknown'})`;
    case 'INVALID_PAYLOAD':
      return 'Cannot analyze: missing content';
    default:
      return 'Unable to calculate trust';
  }
}

module.exports = { renderTrustResult };
