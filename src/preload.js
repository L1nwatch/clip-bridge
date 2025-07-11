const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Clipboard functions
  getClipboard: () => ipcRenderer.invoke('get-clipboard'),
  setClipboard: (text) => ipcRenderer.invoke('set-clipboard', text),
  
  // Server/Client management
  startServer: (config) => ipcRenderer.invoke('start-server', config),
  stopServer: () => ipcRenderer.invoke('stop-server'),
  startClient: (config) => ipcRenderer.invoke('start-client', config),
  stopClient: () => ipcRenderer.invoke('stop-client'),
  getServiceStatus: () => ipcRenderer.invoke('get-service-status'),
  
  // Event listeners for logs and status updates
  onServerLog: (callback) => {
    ipcRenderer.on('server-log', (_, data) => callback(data));
    return () => ipcRenderer.removeAllListeners('server-log');
  },
  onClientLog: (callback) => {
    ipcRenderer.on('client-log', (_, data) => callback(data));
    return () => ipcRenderer.removeAllListeners('client-log');
  },
  onServerStatus: (callback) => {
    ipcRenderer.on('server-status', (_, status) => callback(status));
    return () => ipcRenderer.removeAllListeners('server-status');
  },
  onClientStatus: (callback) => {
    ipcRenderer.on('client-status', (_, status) => callback(status));
    return () => ipcRenderer.removeAllListeners('client-status');
  },
  
  // Client connection management
  getConnectedClients: () => ipcRenderer.invoke('get-connected-clients'),
  onClientConnected: (callback) => {
    ipcRenderer.on('client-connected', (_, clientInfo) => callback(clientInfo));
    return () => ipcRenderer.removeAllListeners('client-connected');
  },
  onClientDisconnected: (callback) => {
    ipcRenderer.on('client-disconnected', (_, clientId) => callback(clientId));
    return () => ipcRenderer.removeAllListeners('client-disconnected');
  }
});
