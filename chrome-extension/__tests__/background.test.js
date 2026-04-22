const { handleCalculateTrust } = require('../lib/trustHandler');

const API_BASE = 'http://localhost:8000';

function mockResponse({ ok = true, status = 200, body = {} } = {}) {
  return {
    ok,
    status,
    json: () => Promise.resolve(body),
  };
}

describe('CALCULATE_TRUST message handler', () => {
  beforeEach(() => {
    global.fetch.mockReset();
  });

  test('valid payload posts to API_BASE + /api/trust/calculate and resolves with the response body', async () => {
    const body = { label: 'Trusted', color: '#28a745', score: 87 };
    global.fetch.mockResolvedValueOnce(mockResponse({ body }));

    const payload = { text: 'hello world', url: 'https://reddit.com/r/test' };
    const result = await handleCalculateTrust(
      { type: 'CALCULATE_TRUST', payload },
      { apiBase: API_BASE, fetch: global.fetch }
    );

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [calledUrl, calledInit] = global.fetch.mock.calls[0];
    expect(calledUrl).toBe(`${API_BASE}/api/trust/calculate`);
    expect(calledInit.method).toBe('POST');
    expect(calledInit.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(calledInit.body)).toEqual(payload);

    expect(result).toEqual(body);
  });

  test('network failure yields { error: "NETWORK" } without throwing', async () => {
    global.fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    const result = await handleCalculateTrust(
      { type: 'CALCULATE_TRUST', payload: { text: 'x' } },
      { apiBase: API_BASE, fetch: global.fetch }
    );

    expect(result).toEqual({ error: 'NETWORK' });
  });

  test('non-2xx response yields an error reply rather than a resolved result', async () => {
    global.fetch.mockResolvedValueOnce(mockResponse({ ok: false, status: 500, body: {} }));

    const result = await handleCalculateTrust(
      { type: 'CALCULATE_TRUST', payload: { text: 'x' } },
      { apiBase: API_BASE, fetch: global.fetch }
    );

    expect(result.error).toBe('SERVER');
    expect(result.status).toBe(500);
    expect(result.label).toBeUndefined();
  });

  test('rejects messages that are not CALCULATE_TRUST', async () => {
    const result = await handleCalculateTrust(
      { type: 'OTHER', payload: { text: 'x' } },
      { apiBase: API_BASE, fetch: global.fetch }
    );

    expect(result).toEqual({ error: 'INVALID_PAYLOAD' });
    expect(global.fetch).not.toHaveBeenCalled();
  });
});
