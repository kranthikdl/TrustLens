// Jest setup: stub the chrome.* globals and fetch so tests never need
// a real browser or network. Ticket 8 wires these in the real extension;
// here we only provide jest-compatible mocks.

const runtimeListeners = [];

global.chrome = {
  runtime: {
    onMessage: {
      addListener: jest.fn((fn) => {
        runtimeListeners.push(fn);
      }),
      removeListener: jest.fn((fn) => {
        const i = runtimeListeners.indexOf(fn);
        if (i >= 0) runtimeListeners.splice(i, 1);
      }),
      _listeners: runtimeListeners,
    },
    sendMessage: jest.fn(),
    lastError: null,
  },
  tabs: {
    query: jest.fn((_q, cb) => cb && cb([{ id: 1, url: 'https://reddit.com/' }])),
    sendMessage: jest.fn(),
  },
  storage: {
    local: {
      get: jest.fn((_keys, cb) => cb && cb({})),
      set: jest.fn(),
    },
  },
  downloads: {
    download: jest.fn(),
  },
};

global.fetch = jest.fn();
