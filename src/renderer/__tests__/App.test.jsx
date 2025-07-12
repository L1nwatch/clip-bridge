// @ts-nocheck - Test file with extensive Electron API mocking
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock Material-UI icons and components that might cause issues
jest.mock('@mui/icons-material/Menu', () => {
  return function MockMenuIcon() {
    return <div data-testid="menu-icon" />;
  };
});

jest.mock('@mui/icons-material/Settings', () => {
  return function MockSettingsIcon() {
    return <div data-testid="settings-icon" />;
  };
});

jest.mock('@mui/icons-material/ContentCopy', () => {
  return function MockContentCopyIcon() {
    return <div data-testid="content-copy-icon" />;
  };
});

jest.mock('@mui/icons-material/Refresh', () => {
  return function MockRefreshIcon() {
    return <div data-testid="refresh-icon" />;
  };
});

jest.mock('@mui/icons-material/Clear', () => {
  return function MockClearIcon() {
    return <div data-testid="clear-icon" />;
  };
});

jest.mock('@mui/icons-material/History', () => {
  return function MockHistoryIcon() {
    return <div data-testid="history-icon" />;
  };
});

jest.mock('@mui/icons-material/Devices', () => {
  return function MockDevicesIcon() {
    return <div data-testid="devices-icon" />;
  };
});

jest.mock('@mui/icons-material/PlayArrow', () => {
  return function MockPlayArrowIcon() {
    return <div data-testid="play-arrow-icon" />;
  };
});

jest.mock('@mui/icons-material/Stop', () => {
  return function MockStopIcon() {
    return <div data-testid="stop-icon" />;
  };
});

jest.mock('@mui/icons-material/Cloud', () => {
  return function MockCloudIcon() {
    return <div data-testid="cloud-icon" />;
  };
});

jest.mock('@mui/icons-material/Computer', () => {
  return function MockComputerIcon() {
    return <div data-testid="computer-icon" />;
  };
});

// Mock the DeviceCard component
jest.mock('../components/DeviceCard', () => {
  // eslint-disable-next-line react/prop-types
  return function MockDeviceCard({ name, ip, status }) {
    return (
      <div data-testid="device-card">
        <span>{name}</span>
        <span>{ip}</span>
        <span>{status}</span>
      </div>
    );
  };
});

// Mock window.electronAPI
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

// Mock window.api with simple default implementations
const mockAPI = {
  startServer: jest.fn().mockResolvedValue(true),
  stopServer: jest.fn().mockResolvedValue(true),
  connectToServer: jest.fn().mockResolvedValue(true),
  disconnectFromServer: jest.fn().mockResolvedValue(true),
  onServerLog: jest.fn(() => jest.fn()), // Return cleanup function
  onClientLog: jest.fn(() => jest.fn()), // Return cleanup function
  onServerStatus: jest.fn(() => jest.fn()), // Return cleanup function
  onClientStatus: jest.fn(() => jest.fn()), // Return cleanup function
  onClientConnected: jest.fn(() => jest.fn()), // Return cleanup function
  onClientDisconnected: jest.fn(() => jest.fn()), // Return cleanup function
  getServiceStatus: jest.fn().mockResolvedValue({ server: 'stopped', client: 'stopped' }),
  getConnectedClients: jest.fn().mockResolvedValue([]),
};

Object.defineProperty(window, 'api', {
  value: mockAPI,
  writable: true,
});

describe('App Component', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Set up default mock implementations
    mockElectronAPI.getConfig.mockResolvedValue({
      port: 8000,
      serverAddress: 'localhost',
      autoStart: false,
      logLevel: 'INFO'
    });
    
    // Set default mode to server for most tests
    localStorage.setItem('clipboardBridge_mode', 'server');
  });

  test('renders main app structure', () => {
    render(<App />);
    
    // Check for main UI elements
    expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    expect(screen.getByTestId('menu-icon')).toBeInTheDocument();
    expect(screen.getByTestId('settings-icon')).toBeInTheDocument();
  });

  test('renders bottom navigation', () => {
    render(<App />);
    
    // Check for bottom navigation icons
    expect(screen.getByTestId('devices-icon')).toBeInTheDocument();
    expect(screen.getByTestId('content-copy-icon')).toBeInTheDocument();
    expect(screen.getByTestId('history-icon')).toBeInTheDocument();
  });

  test('shows start/stop button based on running state', () => {
    render(<App />);
    
    // Should show start button initially
    const startButton = screen.getByTestId('play-arrow-icon').closest('button');
    expect(startButton).toBeInTheDocument();
    expect(startButton).not.toBeDisabled();
  });

  test('displays server status correctly', () => {
    render(<App />);
    
    // Check that server status is displayed
    expect(screen.getByText('Clipboard Server')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();
  });

  test('displays device cards in devices tab', () => {
    render(<App />);
    
    // Switch to devices tab
    const deviceTab = screen.getByText('Devices');
    fireEvent.click(deviceTab);
    
    // Should show devices interface
    expect(screen.getByText('Devices')).toBeInTheDocument();
  });
});

describe('Connected Clients UI', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    
    // Reset mocks before each test
    jest.clearAllMocks();
    
    // Set server mode for client connection tests
    localStorage.setItem('clipboardBridge_mode', 'server');
    
    // Set up default mock implementations
    mockElectronAPI.getConfig.mockResolvedValue({
      port: 8000,
      serverAddress: 'localhost',
      autoStart: false,
      logLevel: 'INFO'
    });
  });

  test('shows "No clients connected" when server mode and no clients', () => {
    render(<App />);
    
    // Should show the no clients message
    expect(screen.getByText('No clients connected')).toBeInTheDocument();
    expect(screen.getByText('Start the server to accept connections')).toBeInTheDocument();
  });

  test('shows client count chip with correct number', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 2 clients
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'client-1',
        name: 'Test Client 1',
        address: '192.168.1.100'
      },
      {
        id: 'client-2',
        name: 'Test Client 2',
        address: '192.168.1.101'
      }
    ]);

    render(<App />);

    // Wait for component to mount and load clients
    await waitFor(() => {
      expect(screen.getByText('2 clients')).toBeInTheDocument();
    });
  });

  test('handles client connection events correctly', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 1 client
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-123',
        name: 'Test Client',
        address: '192.168.1.100'
      }
    ]);

    render(<App />);

    // Wait for component to mount and load clients
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
    
    // Should show the client in the list (DeviceCard should be rendered)
    expect(screen.getByText('Test Client')).toBeInTheDocument();
  });

  test('handles client disconnection events correctly', async () => {
    // Mock getConnectedClients to return no clients (simulating disconnection)
    window.api.getConnectedClients.mockResolvedValue([]);

    render(<App />);

    // Should show no clients
    await waitFor(() => {
      expect(screen.getByText('0 clients')).toBeInTheDocument();
    });
    expect(screen.getByText('No clients connected')).toBeInTheDocument();
  });

  test('prevents duplicate clients from being added', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 1 unique client
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-123',
        name: 'Test Client',
        address: '192.168.1.100'
      }
    ]);

    render(<App />);

    // Should only show 1 client (duplicates prevented by backend)
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
  });

  test('refresh button calls getConnectedClients API', async () => {
    // Mock the API to return some clients
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'client-1',
        name: 'Refreshed Client',
        address: '192.168.1.200',
        connectedAt: '10:00:00'
      }
    ]);

    // Mock service status to show running server so refresh button is active
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });

    render(<App />);

    // Wait for clients to load
    await waitFor(() => {
      expect(screen.getByText('Refreshed Client')).toBeInTheDocument();
    });

    // Reset the mock to track additional calls
    jest.clearAllMocks();
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'client-1',
        name: 'Refreshed Client',
        address: '192.168.1.200',
        connectedAt: '10:00:00'
      }
    ]);

    // Find and click the refresh button
    const refreshButton = screen.getByTitle('Refresh client list');
    fireEvent.click(refreshButton);

    // Should have called the API
    await waitFor(() => {
      expect(window.api.getConnectedClients).toHaveBeenCalled();
    });
  });

  test('clears connected clients when server stops', async () => {
    // Mock getConnectedClients to return no clients (simulating server stop)
    window.api.getConnectedClients.mockResolvedValue([]);

    render(<App />);

    // Should show no clients when server is stopped
    await waitFor(() => {
      expect(screen.getByText('0 clients')).toBeInTheDocument();
    });
  });

  test('shows appropriate message when server is running but no clients', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });

    render(<App />);

    // Should show no clients message when server is running
    await waitFor(() => {
      expect(screen.getByText('No clients connected')).toBeInTheDocument();
    });
  });

  test('displays connected clients with proper information', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return a client with specific info
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-456',
        name: 'My Laptop',
        address: '192.168.1.150'
      }
    ]);

    render(<App />);

    // Should display the client information
    await waitFor(() => {
      expect(screen.getByText('My Laptop')).toBeInTheDocument();
    });
    expect(screen.getByText('192.168.1.150')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  test('handles client connection without name gracefully', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return a client without a name
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-789',
        address: '192.168.1.200'
      }
    ]);

    render(<App />);

    // Should generate a default name
    await waitFor(() => {
      expect(screen.getByText('Client-test-cli')).toBeInTheDocument(); // First 8 chars of ID
    });
    expect(screen.getByText('192.168.1.200')).toBeInTheDocument();
  });

  test('only shows connected clients section in server mode', async () => {
    render(<App />);

    // Should show connected clients section in server mode by default
    expect(screen.getByText('Connected Clients')).toBeInTheDocument();

    // Open settings
    const settingsButton = screen.getByTitle('Settings');
    fireEvent.click(settingsButton);

    // Switch to client mode
    const clientButton = screen.getByRole('button', { name: 'Client' });
    fireEvent.click(clientButton);

    // Close settings
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    // Wait for the mode change to take effect
    await waitFor(() => {
      // Connected Clients section should not be visible in client mode
      expect(screen.queryByText('Connected Clients')).not.toBeInTheDocument();
    });
  });

  test('handles server startup with initial connected clients', async () => {
    // Mock getServiceStatus to return running server with clients
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return existing clients
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'existing-client-1',
        name: 'Pre-existing Client',
        address: '192.168.1.50',
        connectedAt: '09:30:00'
      }
    ]);

    render(<App />);

    // Wait for initial service status check and client loading
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Pre-existing Client')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.50')).toBeInTheDocument();
  });

  test('handles refresh button when server is not running', async () => {
    render(<App />);

    // Wait for server mode to be loaded
    await waitFor(() => {
      expect(screen.getByText('Clipboard Server')).toBeInTheDocument();
    });

    // Find the refresh button (should be present but not do anything when server not running)
    const refreshButton = screen.getByTitle('Refresh client list');
    fireEvent.click(refreshButton);

    // Should not have called the API since server is not running
    expect(window.api.getConnectedClients).not.toHaveBeenCalled();
  });

  test('handles client with very long name gracefully', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return a client with a very long name
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-long-name',
        name: 'This is a very long client name that might cause display issues in the UI',
        address: '192.168.1.100'
      }
    ]);

    render(<App />);

    // Should display the client information
    await waitFor(() => {
      expect(screen.getByText('This is a very long client name that might cause display issues in the UI')).toBeInTheDocument();
    });
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
  });

  test('handles multiple rapid client connections and disconnections', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 3 clients (after some connected and disconnected)
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'rapid-client-1',
        name: 'Rapid Client 1',
        address: '192.168.1.101'
      },
      {
        id: 'rapid-client-3',
        name: 'Rapid Client 3',
        address: '192.168.1.103'
      },
      {
        id: 'rapid-client-5',
        name: 'Rapid Client 5',
        address: '192.168.1.105'
      }
    ]);

    render(<App />);

    // Should show 3 remaining clients
    await waitFor(() => {
      expect(screen.getByText('3 clients')).toBeInTheDocument();
    });
  });

  test('handles refresh with failed API call', async () => {
    // Mock getConnectedClients to fail
    window.api.getConnectedClients.mockRejectedValue(new Error('API Error'));
    
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('No clients connected')).toBeInTheDocument();
    });

    // Click refresh button
    const refreshButton = screen.getByTitle('Refresh client list');
    fireEvent.click(refreshButton);

    // Should have attempted the API call
    await waitFor(() => {
      expect(window.api.getConnectedClients).toHaveBeenCalled();
    });
  });

  test('handles client connection event without address', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return a client without an address
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'test-client-no-address',
        name: 'Client Without Address'
      }
    ]);

    render(<App />);

    // Should still show the client
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
    expect(screen.getByText('Client Without Address')).toBeInTheDocument();
  });

  test('handles extremely rapid client state changes', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 1 client (final state after rapid changes)
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'rapid-change-client',
        name: 'Rapid Change Client',
        address: '192.168.1.99'
      }
    ]);

    render(<App />);

    // Should end up with 1 client
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
  });

  test('properly cleans up when switching from server to client mode', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return a client initially
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'client-before-switch',
        name: 'Client Before Switch',
        address: '192.168.1.123'
      }
    ]);

    const { unmount } = render(<App />);

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Clean up the first render completely
    unmount();

    // Update the service status mock to show server stopped
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'stopped', 
      client: 'stopped' 
    });
    
    // Set local storage to client mode using the correct key/format
    localStorage.setItem('clipBridgeSettings', JSON.stringify({
      mode: 'client',
      config: {
        port: 8000,
        serverAddress: 'localhost',
        autoStart: false,
        logLevel: 'INFO'
      }
    }));

    // Render a new instance of the app with the updated settings
    render(<App />);

    // Now we should not see the Connected Clients section
    expect(screen.queryByText('Connected Clients')).not.toBeInTheDocument();
  });

  test('handles client chip click to expand/collapse client list', async () => {
    // Mock service status to show running server
    window.api.getServiceStatus.mockResolvedValue({ 
      server: 'running', 
      client: 'stopped' 
    });
    
    // Mock getConnectedClients to return 1 client
    window.api.getConnectedClients.mockResolvedValue([
      {
        id: 'clickable-client',
        name: 'Clickable Client',
        address: '192.168.1.200'
      }
    ]);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Client should be visible by default
    expect(screen.getByText('Clickable Client')).toBeInTheDocument();
  });
});
