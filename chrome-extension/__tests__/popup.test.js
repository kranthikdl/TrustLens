const { renderTrustResult } = require('../lib/popupRender');

describe('popup rendering', () => {
  let root;

  beforeEach(() => {
    document.body.innerHTML = '<div id="popup-root"></div>';
    root = document.getElementById('popup-root');
  });

  test('successful TrustCalculateResponse renders the badge label and color', () => {
    const response = { label: 'Trusted', color: '#28a745', score: 87 };

    // Verify chrome.runtime.sendMessage stub resolves with the response,
    // matching the popup contract from Ticket 8.
    chrome.runtime.sendMessage.mockImplementationOnce(() => Promise.resolve(response));

    renderTrustResult(root, response);

    const badge = root.querySelector('[data-testid="trust-badge"]');
    expect(badge).not.toBeNull();
    expect(badge.style.backgroundColor).toBe('rgb(40, 167, 69)');

    const label = root.querySelector('[data-testid="trust-badge-label"]');
    expect(label).not.toBeNull();
    expect(label.textContent).toBe('Trusted');

    const score = root.querySelector('[data-testid="trust-badge-score"]');
    expect(score).not.toBeNull();
    expect(score.textContent).toBe('87');

    expect(root.querySelector('[data-testid="trust-error"]')).toBeNull();
  });

  test('error reply renders the error state and no badge', () => {
    const errorReply = { error: 'NETWORK' };
    chrome.runtime.sendMessage.mockImplementationOnce(() => Promise.resolve(errorReply));

    renderTrustResult(root, errorReply);

    const error = root.querySelector('[data-testid="trust-error"]');
    expect(error).not.toBeNull();
    expect(error.textContent).toMatch(/network error/i);

    expect(root.querySelector('[data-testid="trust-badge"]')).toBeNull();
  });

  test('re-rendering replaces the previous content rather than appending', () => {
    renderTrustResult(root, { label: 'Trusted', color: '#28a745', score: 90 });
    renderTrustResult(root, { error: 'SERVER', status: 500 });

    expect(root.querySelectorAll('[data-testid="trust-badge"]').length).toBe(0);
    expect(root.querySelectorAll('[data-testid="trust-error"]').length).toBe(1);
    expect(root.querySelector('[data-testid="trust-error"]').textContent).toMatch(/500/);
  });
});
