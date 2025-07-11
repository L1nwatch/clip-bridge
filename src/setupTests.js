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
  getServiceStatus: jest.fn(),
  onServerLog: jest.fn(),
  onClientLog: jest.fn(),
  onServerStatus: jest.fn(),
  onClientStatus: jest.fn(),
  onClientConnected: jest.fn(),
  onClientDisconnected: jest.fn(),
  getConnectedClients: jest.fn(),
  startClient: jest.fn(),
  stopClient: jest.fn(),
};

// Also add window.api as an alias for compatibility
Object.defineProperty(window, 'api', {
  value: mockElectronAPI,
  writable: true,
});

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
  
  // Store callbacks for event handlers
  let serverStatusCallback = null;
  let clientStatusCallback = null;
  let clientConnectedCallback = null;
  let clientDisconnectedCallback = null;
  let serverLogCallback = null;
  let clientLogCallback = null;
  
  mockElectronAPI.getConfig.mockResolvedValue({
    port: 8000,
    serverAddress: 'localhost',
    autoStart: false,
    logLevel: 'INFO'
  });
  
  mockElectronAPI.startServer.mockResolvedValue({ success: true });
  mockElectronAPI.stopServer.mockResolvedValue({ success: true });
  mockElectronAPI.startClient.mockResolvedValue({ success: true });
  mockElectronAPI.stopClient.mockResolvedValue({ success: true });
  mockElectronAPI.saveConfig.mockResolvedValue({ success: true });
  mockElectronAPI.getServiceStatus.mockResolvedValue({ server: 'stopped', client: 'stopped' });
  mockElectronAPI.getConnectedClients.mockResolvedValue([]);
  
  // Mock event listener functions to return cleanup functions and store callbacks
  mockElectronAPI.onServerLog.mockImplementation((callback) => {
    serverLogCallback = callback;
    return () => { serverLogCallback = null; };
  });
  
  mockElectronAPI.onClientLog.mockImplementation((callback) => {
    clientLogCallback = callback;
    return () => { clientLogCallback = null; };
  });
  
  mockElectronAPI.onServerStatus.mockImplementation((callback) => {
    serverStatusCallback = callback;
    return () => { serverStatusCallback = null; };
  });
  
  mockElectronAPI.onClientStatus.mockImplementation((callback) => {
    clientStatusCallback = callback;
    return () => { clientStatusCallback = null; };
  });
  
  mockElectronAPI.onClientConnected.mockImplementation((callback) => {
    clientConnectedCallback = callback;
    return () => { clientConnectedCallback = null; };
  });
  
  mockElectronAPI.onClientDisconnected.mockImplementation((callback) => {
    clientDisconnectedCallback = callback;
    return () => { clientDisconnectedCallback = null; };
  });
  
  // Add trigger methods for testing
  mockElectronAPI._triggerServerStatus = (status) => {
    if (serverStatusCallback) serverStatusCallback(status);
  };
  
  mockElectronAPI._triggerClientStatus = (status) => {
    if (clientStatusCallback) clientStatusCallback(status);
  };
  
  mockElectronAPI._triggerClientConnected = (clientInfo) => {
    if (clientConnectedCallback) clientConnectedCallback(clientInfo);
  };
  
  mockElectronAPI._triggerClientDisconnected = (clientId) => {
    if (clientDisconnectedCallback) clientDisconnectedCallback(clientId);
  };
  
  mockElectronAPI._triggerServerLog = (log) => {
    if (serverLogCallback) serverLogCallback(log);
  };
  
  mockElectronAPI._triggerClientLog = (log) => {
    if (clientLogCallback) clientLogCallback(log);
  };
});
