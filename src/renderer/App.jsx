import React, { useState, useEffect, useRef } from 'react';
import { 
  AppBar, 
  Toolbar, 
  IconButton, 
  Typography, 
  Box, 
  Stack,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Chip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  BottomNavigation, 
  BottomNavigationAction, 
  CircularProgress
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SettingsIcon from '@mui/icons-material/Settings';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RefreshIcon from '@mui/icons-material/Refresh';
import ClearIcon from '@mui/icons-material/Clear';
import HistoryIcon from '@mui/icons-material/History';
import DevicesIcon from '@mui/icons-material/Devices';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import CloudIcon from '@mui/icons-material/Cloud';
import ComputerIcon from '@mui/icons-material/Computer';

import DeviceCard from './components/DeviceCard';

// Load settings from localStorage with defaults
const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('clipBridgeSettings');
    if (savedSettings) {
      return JSON.parse(savedSettings);
    }
  } catch (error) {
    console.warn('Failed to load settings from localStorage:', error);
  }
  
  // Default settings
  return {
    mode: 'server',
    config: {
      port: 8000,
      serverAddress: 'localhost',
      autoStart: false,
      logLevel: 'INFO'
    }
  };
};

// Save settings to localStorage
const saveSettings = (mode, config) => {
  try {
    const settings = { mode, config };
    localStorage.setItem('clipBridgeSettings', JSON.stringify(settings));
  } catch (error) {
    console.warn('Failed to save settings to localStorage:', error);
  }
};

export default function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  
  // Load initial settings from localStorage
  const initialSettings = loadSettings();
  const [mode, setMode] = useState(initialSettings.mode);
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState(initialSettings.config);
  const [status, setStatus] = useState('idle'); // 'idle', 'starting', 'running', 'stopping', 'error'
  const [logs, setLogs] = useState([]);
  const [connectedDevices, setConnectedDevices] = useState([]);
  
  // Ref for auto-scrolling logs
  const logContainerRef = useRef(null);

  // Auto-scroll to latest log
  useEffect(() => {
    if (logContainerRef.current && logs.length > 0) {
      // Use smooth scrolling for better UX, fallback for test environments
      if (typeof logContainerRef.current.scrollTo === 'function') {
        logContainerRef.current.scrollTo({
          top: logContainerRef.current.scrollHeight,
          behavior: 'smooth'
        });
      } else {
        // Fallback for test environments (JSDOM)
        logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
      }
    }
  }, [logs]);

  // Save settings whenever mode or config changes
  useEffect(() => {
    saveSettings(mode, config);
  }, [mode, config]);

  // Mock devices for demonstration
  const mockDevices = [
    { name: 'PTOP-880OUEHO.china...', ip: '192.168.2.33', status: 'connected' },
    { name: 'LAPTOP-12345.home', ip: '192.168.2.34', status: 'disconnected' }
  ];

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  // Setup event listeners for logs and status updates
  useEffect(() => {
    const removeServerLogListener = window.api?.onServerLog?.(addLog);
    const removeClientLogListener = window.api?.onClientLog?.(addLog);
    const removeServerStatusListener = window.api?.onServerStatus?.((status) => {
      setStatus(status);
      if (status === 'stopped') {
        setIsRunning(false);
        setConnectedDevices([]); // Clear connected devices when server stops
      } else if (status === 'running') {
        setIsRunning(true);
      }
    });
    const removeClientStatusListener = window.api?.onClientStatus?.((status) => {
      setStatus(status);
      if (status === 'stopped') setIsRunning(false);
    });

    // Add listeners for client connections (only in server mode)
    const removeClientConnectedListener = window.api?.onClientConnected?.((clientInfo) => {
      setConnectedDevices(prev => {
        // Check if client already exists (avoid duplicates)
        const exists = prev.some(device => device.id === clientInfo.id);
        if (exists) return prev;
        
        addLog(`Client connected: ${clientInfo.address || 'Unknown'}`);
        return [...prev, {
          id: clientInfo.id,
          name: clientInfo.name || `Client-${clientInfo.id.slice(0, 8)}`,
          ip: clientInfo.address || 'Unknown',
          status: 'connected',
          connectedAt: new Date().toLocaleTimeString()
        }];
      });
    });

    const removeClientDisconnectedListener = window.api?.onClientDisconnected?.((clientId) => {
      setConnectedDevices(prev => {
        const client = prev.find(device => device.id === clientId);
        if (client) {
          addLog(`Client disconnected: ${client.ip}`);
        }
        return prev.filter(device => device.id !== clientId);
      });
    });

    // Check initial service status
    const serviceStatusPromise = window.api?.getServiceStatus?.();
    if (serviceStatusPromise) {
      serviceStatusPromise.then(status => {
        if (mode === 'server' && status.server === 'running') {
          setIsRunning(true);
          setStatus('running');
          // Get initial connected clients if any
          const connectedClientsPromise = window.api?.getConnectedClients?.();
          if (connectedClientsPromise) {
            connectedClientsPromise.then(clients => {
              if (clients && clients.length > 0) {
                setConnectedDevices(clients.map(client => ({
                  id: client.id,
                  name: client.name || `Client-${client.id.slice(0, 8)}`,
                  ip: client.address || 'Unknown',
                  status: 'connected',
                  connectedAt: client.connectedAt || 'Unknown'
                })));
              }
            }).catch(() => {
              // Ignore error, just means no clients or API not available
            });
          }
        } else if (mode === 'client' && status.client === 'running') {
          setIsRunning(true);
          setStatus('running');
        }
      }).catch(() => {
        // Ignore error, API not available
      });
    }

    return () => {
      removeServerLogListener?.();
      removeClientLogListener?.();
      removeServerStatusListener?.();
      removeClientStatusListener?.();
      removeClientConnectedListener?.();
      removeClientDisconnectedListener?.();
    };
  }, [mode]);

  const startService = async () => {
    setStatus('starting');
    setIsRunning(true);
    
    try {
      let result;
      if (mode === 'server') {
        result = await window.api?.startServer?.(config);
      } else {
        result = await window.api?.startClient?.(config);
      }
      
      if (result?.success) {
        setStatus('running');
        addLog(result.message);
      } else {
        throw new Error(result?.error || 'Failed to start service');
      }
    } catch (error) {
      setStatus('error');
      setIsRunning(false);
      addLog(`Failed to start ${mode}: ${error.message}`);
    }
  };

  const stopService = async () => {
    setStatus('stopping');
    
    try {
      let result;
      if (mode === 'server') {
        result = await window.api?.stopServer?.();
      } else {
        result = await window.api?.stopClient?.();
      }
      
      if (result?.success) {
        setStatus('idle');
        setIsRunning(false);
        addLog(result.message);
      } else {
        throw new Error(result?.error || 'Failed to stop service');
      }
    } catch (error) {
      setStatus('error');
      addLog(`Failed to stop ${mode}: ${error.message}`);
    }
  };

  const addLog = (message) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-99), { timestamp, message }]);
  };

  const renderMainContent = () => {
    switch (currentTab) {
      case 0: // Clipboard
        return (
          <Stack spacing={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">
                    {mode === 'server' ? 'Clipboard Server' : 'Clipboard Client'}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip 
                      label={status} 
                      color={status === 'running' ? 'success' : status === 'error' ? 'error' : 'default'}
                      size="small"
                    />
                    {status === 'starting' || status === 'stopping' ? (
                      <CircularProgress size={20} />
                    ) : (
                      <IconButton 
                        color={isRunning ? 'error' : 'success'}
                        onClick={isRunning ? stopService : startService}
                        disabled={status === 'starting' || status === 'stopping'}
                      >
                        {isRunning ? <StopIcon /> : <PlayArrowIcon />}
                      </IconButton>
                    )}
                  </Box>
                </Box>
                
                {mode === 'server' ? (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Server running on port {config.port}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      WebSocket: ws://localhost:{config.port}/ws
                    </Typography>
                  </Box>
                ) : (
                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Connecting to {config.serverAddress}:{config.port}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {mode === 'server' && (
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">Connected Clients</Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip 
                        label={`${connectedDevices.length} client${connectedDevices.length !== 1 ? 's' : ''}`}
                        size="small"
                        color={connectedDevices.length > 0 ? 'success' : 'default'}
                      />
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          // Refresh connected clients list
                          if (isRunning && mode === 'server') {
                            const connectedClientsPromise = window.api?.getConnectedClients?.();
                            if (connectedClientsPromise) {
                              connectedClientsPromise.then(clients => {
                                if (clients) {
                                  setConnectedDevices(clients.map(client => ({
                                    id: client.id,
                                    name: client.name || `Client-${client.id.slice(0, 8)}`,
                                    ip: client.address || 'Unknown',
                                    status: 'connected',
                                    connectedAt: client.connectedAt || 'Unknown'
                                  })));
                                  addLog('Refreshed client list');
                                }
                              }).catch(() => {
                                addLog('Failed to refresh client list');
                              });
                            }
                          }
                        }}
                        title="Refresh client list"
                      >
                        <RefreshIcon />
                      </IconButton>
                    </Box>
                  </Box>
                  {connectedDevices.length === 0 ? (
                    <Alert severity="info" sx={{ textAlign: 'center' }}>
                      <Typography variant="body2">
                        No clients connected
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {isRunning ? 'Waiting for clients to connect...' : 'Start the server to accept connections'}
                      </Typography>
                    </Alert>
                  ) : (
                    <Stack spacing={2}>
                      {connectedDevices.map((device) => (
                        <DeviceCard key={device.id} {...device} />
                      ))}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            )}

            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Activity Log</Typography>
                  <IconButton 
                    size="small" 
                    onClick={() => setLogs([])} 
                    title="Clear activity log"
                    sx={{
                      '&:hover': {
                        bgcolor: 'error.light',
                        color: 'white'
                      }
                    }}
                  >
                    <ClearIcon />
                  </IconButton>
                </Box>
                <Box 
                  ref={logContainerRef}
                  sx={{ 
                    maxHeight: 200, 
                    overflow: 'auto', 
                    bgcolor: 'grey.50', 
                    p: 2, 
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'grey.200',
                    scrollBehavior: 'smooth',
                    '&::-webkit-scrollbar': {
                      width: '6px',
                    },
                    '&::-webkit-scrollbar-track': {
                      bgcolor: 'grey.100',
                      borderRadius: 3,
                    },
                    '&::-webkit-scrollbar-thumb': {
                      bgcolor: 'grey.300',
                      borderRadius: 3,
                      '&:hover': {
                        bgcolor: 'grey.400',
                      },
                    },
                  }}>
                  {logs.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 4 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                        📋 Activity log is empty
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Server events and clipboard operations will appear here
                      </Typography>
                    </Box>
                  ) : (
                    <Stack spacing={1}>
                      {logs.map((log, idx) => (
                        <Box 
                          key={idx}
                          sx={{ 
                            p: 1, 
                            bgcolor: 'white', 
                            borderRadius: 1, 
                            border: '1px solid',
                            borderColor: 'grey.100',
                            animation: idx === logs.length - 1 ? 'fadeInUp 0.3s ease-out' : 'none',
                            '@keyframes fadeInUp': {
                              '0%': {
                                opacity: 0,
                                transform: 'translateY(10px)',
                              },
                              '100%': {
                                opacity: 1,
                                transform: 'translateY(0)',
                              },
                            },
                            '&:hover': {
                              bgcolor: 'grey.25'
                            }
                          }}
                        >
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontFamily: 'monospace', 
                              fontSize: '0.75rem',
                              lineHeight: 1.4
                            }}
                          >
                            <span style={{ color: '#666', fontSize: '0.7rem' }}>
                              [{log.timestamp}]
                            </span>
                            <br />
                            <span style={{ color: '#333' }}>
                              {log.message}
                            </span>
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Stack>
        );

      case 1: // History
        return (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Clipboard History</Typography>
              <Alert severity="info">History feature coming soon</Alert>
            </CardContent>
          </Card>
        );

      case 2: // Devices
        return (
          <Stack spacing={2}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Available Devices</Typography>
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Box>
                <Stack spacing={2}>
                  {mockDevices.map((device, idx) => (
                    <DeviceCard key={idx} {...device} />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        );

      default:
        return null;
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <AppBar position="static">
        <Toolbar>
          <IconButton edge="start" color="inherit">
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1 }} align="center">
            Clipboard Bridge
          </Typography>
          <IconButton color="inherit" onClick={() => setSettingsOpen(true)} title="Settings">
            <SettingsIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
        {renderMainContent()}
      </Box>

      <BottomNavigation value={currentTab} onChange={(_, value) => setCurrentTab(value)}>
        <BottomNavigationAction label="Clipboard" icon={<ContentCopyIcon />} />
        <BottomNavigationAction label="History" icon={<HistoryIcon />} />
        <BottomNavigationAction label="Devices" icon={<DevicesIcon />} />
      </BottomNavigation>

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Settings</DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            {/* Mode Selection */}
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Mode</Typography>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant={mode === 'server' ? 'contained' : 'outlined'}
                    startIcon={<CloudIcon />}
                    onClick={() => setMode('server')}
                    disabled={isRunning}
                  >
                    Server
                  </Button>
                  <Button
                    variant={mode === 'client' ? 'contained' : 'outlined'}
                    startIcon={<ComputerIcon />}
                    onClick={() => setMode('client')}
                    disabled={isRunning}
                  >
                    Client
                  </Button>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  {mode === 'server' ? 'Host clipboard sharing for other devices' : 'Connect to a clipboard server'}
                </Typography>
              </CardContent>
            </Card>

            {/* Configuration */}
            <Card variant="outlined">
              <CardContent>
                <Typography variant="h6" gutterBottom>Configuration</Typography>
                <Stack spacing={2}>
                  <TextField
                    label="Port"
                    type="number"
                    value={config.port}
                    onChange={(e) => handleConfigChange('port', parseInt(e.target.value))}
                    disabled={isRunning}
                    size="small"
                  />
                  {mode === 'client' && (
                    <TextField
                      label="Server Address"
                      value={config.serverAddress}
                      onChange={(e) => handleConfigChange('serverAddress', e.target.value)}
                      disabled={isRunning}
                      size="small"
                      placeholder="localhost or IP address"
                    />
                  )}
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.autoStart}
                        onChange={(e) => handleConfigChange('autoStart', e.target.checked)}
                      />
                    }
                    label="Auto-start on launch"
                  />
                </Stack>
              </CardContent>
            </Card>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
