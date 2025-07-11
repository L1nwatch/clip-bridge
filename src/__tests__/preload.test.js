// Mock electron modules
const mockContextBridge = {
  exposeInMainWorld: jest.fn()
};

const mockIpcRenderer = {
  invoke: jest.fn(),
  on: jest.fn(),
  removeAllListeners: jest.fn()
};

jest.mock('electron', () => ({
  contextBridge: mockContextBridge,
  ipcRenderer: mockIpcRenderer
}));

describe('Preload API Integration', () => {
  let apiObject;

  beforeEach(() => {
    // Clear all mocks and module cache
    jest.clearAllMocks();
    delete require.cache[require.resolve('../preload')];
    
    // Load the preload script fresh
    require('../preload');
    
    // Get the API object from the mock call
    const calls = mockContextBridge.exposeInMainWorld.mock.calls;
    if (calls.length > 0) {
      [, apiObject] = calls[0];
    }
  });

  test('should expose clipboard functions to main world', () => {
    expect(mockContextBridge.exposeInMainWorld).toHaveBeenCalledWith('api', expect.any(Object));
    
    // Check that all expected methods are exposed
    expect(apiObject).toHaveProperty('getClipboard');
    expect(apiObject).toHaveProperty('setClipboard');
    expect(apiObject).toHaveProperty('startServer');
    expect(apiObject).toHaveProperty('stopServer');
    expect(apiObject).toHaveProperty('startClient');
    expect(apiObject).toHaveProperty('stopClient');
    expect(apiObject).toHaveProperty('getServiceStatus');
    expect(apiObject).toHaveProperty('getConnectedClients');
    expect(apiObject).toHaveProperty('onClientConnected');
    expect(apiObject).toHaveProperty('onClientDisconnected');
  });

  test('should handle IPC invoke calls correctly', () => {
    
    // Test clipboard functions
    apiObject.getClipboard();
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('get-clipboard');
    
    apiObject.setClipboard('test text');
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('set-clipboard', 'test text');
    
    // Test server functions
    const serverConfig = { port: 3000 };
    apiObject.startServer(serverConfig);
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('start-server', serverConfig);
    
    apiObject.stopServer();
    expect(mockIpcRenderer.invoke).toHaveBeenCalledWith('stop-server');
  });
});
