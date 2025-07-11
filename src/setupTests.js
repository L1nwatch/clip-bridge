import '@testing-library/jest-dom';

// Mock window.electronAPI for all tests
const mockElectronAPI = {
  startServer: jest.fn(),
  stopServer: jest.fn(),
  connectToServer: jest.fn(),
  disconnectFromServer: jest.fn(),
  onServerMessage: jest.fn(),
  onServerError: jest.fn(),
  onServerStopped: jest.fn(),
  sendToServer: jest.fn(),
  getConfig: jest.fn(),
  saveConfig: jest.fn(),
};

Object.defineProperty(window, 'electronAPI', {
  value: mockElectronAPI,
  writable: true,
});

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup default mock return values
beforeEach(() => {
  jest.clearAllMocks();
  
  mockElectronAPI.getConfig.mockResolvedValue({
    port: 8000,
    serverAddress: 'localhost',
    autoStart: false,
    logLevel: 'INFO'
  });
  
  mockElectronAPI.startServer.mockResolvedValue({ success: true });
  mockElectronAPI.stopServer.mockResolvedValue({ success: true });
  mockElectronAPI.saveConfig.mockResolvedValue({ success: true });
});
