module.exports = {
  testEnvironment: 'jsdom',
  setupFiles: ['<rootDir>/__tests__/setup.js'],
  testMatch: ['<rootDir>/__tests__/**/*.test.js'],
  testPathIgnorePatterns: ['/node_modules/', '/__tests__/setup.js'],
  clearMocks: true,
};
