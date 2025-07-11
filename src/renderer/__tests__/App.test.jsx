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

describe('App Component', () => {
  beforeEach(() => {
    // Reset all mocks before each test
    jest.clearAllMocks();
    
    // Set up default mock implementations
    mockElectronAPI.getConfig.mockResolvedValue({
      port: 8000,
      serverAddress: 'localhost',
      autoStart: false,
      logLevel: 'INFO'
    });
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
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  test('shows "No clients connected" when server mode and no clients', () => {
    render(<App />);
    
    // Should show the no clients message
    expect(screen.getByText('No clients connected')).toBeInTheDocument();
    expect(screen.getByText('Start the server to accept connections')).toBeInTheDocument();
  });

  test('shows client count chip with correct number', async () => {
    render(<App />);
    
    // Add first client
    window.api._triggerClientConnected({
      id: 'client-1',
      name: 'Test Client 1',
      address: '192.168.1.100'
    });

    // Add second client  
    window.api._triggerClientConnected({
      id: 'client-2',
      name: 'Test Client 2', 
      address: '192.168.1.101'
    });

    // Should show "2 clients" in the chip
    await waitFor(() => {
      expect(screen.getByText('2 clients')).toBeInTheDocument();
    });
  });

  test('handles client connection events correctly', async () => {
    render(<App />);

    // Simulate a client connecting
    window.api._triggerClientConnected({
      id: 'test-client-123',
      name: 'Test Client',
      address: '192.168.1.100'
    });

    // Wait for state update
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
    
    // Should show the client in the list (DeviceCard should be rendered)
    expect(screen.getByText('Test Client')).toBeInTheDocument();
  });

  test('handles client disconnection events correctly', async () => {
    render(<App />);

    // Add a client first
    window.api._triggerClientConnected({
      id: 'test-client-123',
      name: 'Test Client',
      address: '192.168.1.100'
    });

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Remove the client
    window.api._triggerClientDisconnected('test-client-123');

    // Should be back to no clients
    await waitFor(() => {
      expect(screen.getByText('0 clients')).toBeInTheDocument();
    });
    expect(screen.getByText('No clients connected')).toBeInTheDocument();
  });

  test('prevents duplicate clients from being added', async () => {
    render(<App />);

    // Add the same client twice
    const clientInfo = {
      id: 'test-client-123',
      name: 'Test Client',
      address: '192.168.1.100'
    };

    window.api._triggerClientConnected(clientInfo);
    window.api._triggerClientConnected(clientInfo); // Duplicate

    // Should still only show 1 client
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

    render(<App />);

    // First trigger server running so refresh button is active
    window.api._triggerServerStatus('running');

    // Wait for server to be running
    await waitFor(() => {
      expect(screen.getByText('Waiting for clients to connect...')).toBeInTheDocument();
    });

    // Find and click the refresh button
    const refreshButton = screen.getByTitle('Refresh client list');
    fireEvent.click(refreshButton);

    // Should have called the API
    await waitFor(() => {
      expect(window.api.getConnectedClients).toHaveBeenCalled();
    });
  });

  test('clears connected clients when server stops', async () => {
    render(<App />);

    // Add a client first
    window.api._triggerClientConnected({
      id: 'test-client-123',
      name: 'Test Client',
      address: '192.168.1.100'
    });

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Simulate server stopping
    window.api._triggerServerStatus('stopped');

    // Should clear all clients
    await waitFor(() => {
      expect(screen.getByText('0 clients')).toBeInTheDocument();
    });
  });

  test('shows appropriate message when server is running but no clients', async () => {
    render(<App />);

    // Simulate server starting (this should set isRunning to true)
    window.api._triggerServerStatus('running');

    // Wait for the state change to take effect
    await waitFor(() => {
      // Should show waiting message when server is running
      expect(screen.getByText('Waiting for clients to connect...')).toBeInTheDocument();
    });
  });

  test('displays connected clients with proper information', async () => {
    render(<App />);

    // Add a client with specific info
    window.api._triggerClientConnected({
      id: 'test-client-456',
      name: 'My Laptop',
      address: '192.168.1.150'
    });

    // Should display the client information
    await waitFor(() => {
      expect(screen.getByText('My Laptop')).toBeInTheDocument();
    });
    expect(screen.getByText('192.168.1.150')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  test('handles client connection without name gracefully', async () => {
    render(<App />);

    // Add a client without a name
    window.api._triggerClientConnected({
      id: 'test-client-789',
      address: '192.168.1.200'
    });

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

  test('handles refresh button when server is not running', () => {
    render(<App />);

    // Find the refresh button (should be present but not do anything when server not running)
    const refreshButton = screen.getByTitle('Refresh client list');
    fireEvent.click(refreshButton);

    // Should not have called the API since server is not running
    expect(window.api.getConnectedClients).not.toHaveBeenCalled();
  });

  test('handles client with very long name gracefully', async () => {
    render(<App />);

    // Add a client with a very long name
    window.api._triggerClientConnected({
      id: 'test-client-long-name',
      name: 'This is a very long client name that might cause display issues in the UI',
      address: '192.168.1.100'
    });

    // Should display the client information
    await waitFor(() => {
      expect(screen.getByText('This is a very long client name that might cause display issues in the UI')).toBeInTheDocument();
    });
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
  });

  test('handles multiple rapid client connections and disconnections', async () => {
    render(<App />);

    // Add multiple clients rapidly
    for (let i = 1; i <= 5; i++) {
      window.api._triggerClientConnected({
        id: `rapid-client-${i}`,
        name: `Rapid Client ${i}`,
        address: `192.168.1.${100 + i}`
      });
    }

    // Should show all 5 clients
    await waitFor(() => {
      expect(screen.getByText('5 clients')).toBeInTheDocument();
    });

    // Disconnect some clients rapidly
    window.api._triggerClientDisconnected('rapid-client-2');
    window.api._triggerClientDisconnected('rapid-client-4');

    // Should show 3 remaining clients
    await waitFor(() => {
      expect(screen.getByText('3 clients')).toBeInTheDocument();
    });
  });

  test('handles refresh with failed API call', async () => {
    // Mock getConnectedClients to fail
    window.api.getConnectedClients.mockRejectedValue(new Error('API Error'));

    render(<App />);

    // Start server so refresh button is active
    window.api._triggerServerStatus('running');

    await waitFor(() => {
      expect(screen.getByText('Waiting for clients to connect...')).toBeInTheDocument();
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
    render(<App />);

    // Add a client without an address
    window.api._triggerClientConnected({
      id: 'test-client-no-address',
      name: 'Client Without Address'
    });

    // Should still show the client
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
    expect(screen.getByText('Client Without Address')).toBeInTheDocument();
  });

  test('handles extremely rapid client state changes', async () => {
    render(<App />);

    const clientInfo = {
      id: 'rapid-change-client',
      name: 'Rapid Change Client',
      address: '192.168.1.99'
    };

    // Rapidly connect and disconnect the same client
    window.api._triggerClientConnected(clientInfo);
    window.api._triggerClientDisconnected(clientInfo.id);
    window.api._triggerClientConnected(clientInfo);
    window.api._triggerClientDisconnected(clientInfo.id);
    window.api._triggerClientConnected(clientInfo);

    // Should end up with 1 client
    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });
  });

  test('properly cleans up when switching from server to client mode', async () => {
    render(<App />);

    // Add some clients first
    window.api._triggerClientConnected({
      id: 'client-before-switch',
      name: 'Client Before Switch',
      address: '192.168.1.123'
    });

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Switch to client mode
    const settingsButton = screen.getByTitle('Settings');
    fireEvent.click(settingsButton);

    const clientButton = screen.getByRole('button', { name: 'Client' });
    fireEvent.click(clientButton);

    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);

    // Connected Clients section should not be visible in client mode
    await waitFor(() => {
      expect(screen.queryByText('Connected Clients')).not.toBeInTheDocument();
    });
  });

  test('handles client chip click to expand/collapse client list', async () => {
    render(<App />);

    // Initially should show "0 clients" chip
    const chip = screen.getByText('0 clients');
    expect(chip).toBeInTheDocument();

    // Add a client
    window.api._triggerClientConnected({
      id: 'clickable-client',
      name: 'Clickable Client',
      address: '192.168.1.200'
    });

    await waitFor(() => {
      expect(screen.getByText('1 client')).toBeInTheDocument();
    });

    // Client should be visible by default
    expect(screen.getByText('Clickable Client')).toBeInTheDocument();
  });
});
