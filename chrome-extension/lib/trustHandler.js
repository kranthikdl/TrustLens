// CALCULATE_TRUST message handler logic, extracted as a pure function so
// it can be unit-tested without a running service worker. Ticket 8's
// background wiring should delegate to `handleCalculateTrust` after
// receiving a message of type `CALCULATE_TRUST`.

const DEFAULT_API_BASE = 'http://localhost:8000';

async function handleCalculateTrust(message, deps = {}) {
  const apiBase = deps.apiBase || DEFAULT_API_BASE;
  const fetchImpl = deps.fetch || (typeof fetch !== 'undefined' ? fetch : null);

  if (!fetchImpl) {
    return { error: 'NETWORK' };
  }

  if (!message || message.type !== 'CALCULATE_TRUST' || !message.payload) {
    return { error: 'INVALID_PAYLOAD' };
  }

  let response;
  try {
    response = await fetchImpl(`${apiBase}/api/trust/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message.payload),
    });
  } catch (_err) {
    return { error: 'NETWORK' };
  }

  if (!response || !response.ok) {
    const status = response && typeof response.status === 'number' ? response.status : 0;
    return { error: 'SERVER', status };
  }

  try {
    return await response.json();
  } catch (_err) {
    return { error: 'PARSE' };
  }
}

module.exports = { handleCalculateTrust, DEFAULT_API_BASE };
