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
  beforeEach(() => {
    jest.clearAllMocks();
    // Clear module cache to ensure fresh require
    delete require.cache[require.resolve('../preload')];
  });

  test('should expose clipboard functions to main world', () => {
    require('../preload');
    
    expect(mockContextBridge.exposeInMainWorld).toHaveBeenCalledWith('api', expect.any(Object));
    
    const [, apiObject] = mockContextBridge.exposeInMainWorld.mock.calls[0];
    
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
    require('../preload');
    const [, apiObject] = mockContextBridge.exposeInMainWorld.mock.calls[0];
    
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
