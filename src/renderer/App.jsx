import React, { useState, useEffect } from 'react';
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
import HistoryIcon from '@mui/icons-material/History';
import DevicesIcon from '@mui/icons-material/Devices';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import CloudIcon from '@mui/icons-material/Cloud';
import ComputerIcon from '@mui/icons-material/Computer';

import DeviceCard from './components/DeviceCard';

export default function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [mode, setMode] = useState('server'); // 'server' or 'client'
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState({
    port: 8000,  // Server mode: port to run server on, Client mode: port server is running on
    serverAddress: 'localhost',
    autoStart: false,
    logLevel: 'INFO'
  });
  const [status, setStatus] = useState('idle'); // 'idle', 'starting', 'running', 'stopping', 'error'
  const [logs, setLogs] = useState([]);
  const [connectedDevices] = useState([]);

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
      if (status === 'stopped') setIsRunning(false);
    });
    const removeClientStatusListener = window.api?.onClientStatus?.((status) => {
      setStatus(status);
      if (status === 'stopped') setIsRunning(false);
    });

    // Check initial service status
    window.api?.getServiceStatus?.().then(status => {
      if (mode === 'server' && status.server === 'running') {
        setIsRunning(true);
        setStatus('running');
      } else if (mode === 'client' && status.client === 'running') {
        setIsRunning(true);
        setStatus('running');
      }
    });

    return () => {
      removeServerLogListener?.();
      removeClientLogListener?.();
      removeServerStatusListener?.();
      removeClientStatusListener?.();
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
                  <Typography variant="h6" gutterBottom>Connected Clients</Typography>
                  {connectedDevices.length === 0 ? (
                    <Alert severity="info">No clients connected</Alert>
                  ) : (
                    <Stack spacing={1}>
                      {connectedDevices.map((device, idx) => (
                        <DeviceCard key={idx} {...device} />
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
                  <IconButton size="small" onClick={() => setLogs([])}>
                    <RefreshIcon />
                  </IconButton>
                </Box>
                <Box sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'grey.50', p: 2, borderRadius: 1 }}>
                  {logs.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">No activity yet</Typography>
                  ) : (
                    <Stack spacing={0.5}>
                      {logs.map((log, idx) => (
                        <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          <span style={{ color: '#666' }}>[{log.timestamp}]</span> {log.message}
                        </Typography>
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
          <IconButton color="inherit" onClick={() => setSettingsOpen(true)}>
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
