/**
 * Vitest Test Setup
 */

import '@testing-library/jest-dom';

// Mock window.api for renderer tests
const mockApi = {
  getVersion: vi.fn().mockResolvedValue('0.1.0'),
  getPlatform: vi.fn().mockResolvedValue('win32'),
};

Object.defineProperty(window, 'api', {
  value: mockApi,
  writable: true,
});

// Reset mocks between tests
beforeEach(() => {
  vi.clearAllMocks();
});
