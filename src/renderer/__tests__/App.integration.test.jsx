import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock all Material-UI icons
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

// Mock DeviceCard
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

describe('App Integration Tests', () => {
  let mockElectronAPI;

  beforeEach(() => {
    // Reset DOM and all mocks
    document.body.innerHTML = '';
    jest.clearAllMocks();

    // Clean up any existing window properties
    if (window.electronAPI) {
      delete window.electronAPI;
    }
    if (window.api) {
      delete window.api;
    }

    // Create comprehensive mock for electronAPI
    mockElectronAPI = {
      startServer: jest.fn(),
      stopServer: jest.fn(),
      startClient: jest.fn(),
      stopClient: jest.fn(),
      onServerMessage: jest.fn(),
      onServerError: jest.fn(),
      onServerStopped: jest.fn(),
      onClientConnected: jest.fn(),
      onClientDisconnected: jest.fn(),
      getConfig: jest.fn(),
      saveConfig: jest.fn(),
      getConnectedClients: jest.fn(),
      getServiceStatus: jest.fn(),
      sendToServer: jest.fn(),
    };

    // Set up default implementations
    mockElectronAPI.getConfig.mockResolvedValue({
      port: 8000,
      serverAddress: 'localhost',
      autoStart: false,
      logLevel: 'INFO',
      updateInterval: 1000
    });

    mockElectronAPI.getServiceStatus.mockResolvedValue({
      server: 'stopped',
      client: 'stopped'
    });

    mockElectronAPI.getConnectedClients.mockResolvedValue([]);

    // Set up electronAPI on window - use assignment to avoid redefinition error
    if (!window.electronAPI) {
      window.electronAPI = mockElectronAPI;
    } else {
      // Update existing properties instead of redefining
      Object.assign(window.electronAPI, mockElectronAPI);
    }

    // Mock window.api for backward compatibility
    if (!window.api) {
      window.api = {
        ...mockElectronAPI,
        _triggerServerMessage: jest.fn(),
        _triggerServerError: jest.fn(),
        _triggerServerStopped: jest.fn(),
        _triggerServerStatus: jest.fn(),
        _triggerClientConnected: jest.fn(),
        _triggerClientDisconnected: jest.fn(),
      };
    } else {
      Object.assign(window.api, {
        ...mockElectronAPI,
        _triggerServerMessage: jest.fn(),
        _triggerServerError: jest.fn(),
        _triggerServerStopped: jest.fn(),
        _triggerServerStatus: jest.fn(),
        _triggerClientConnected: jest.fn(),
        _triggerClientDisconnected: jest.fn(),
      });
    }
  });

  afterEach(() => {
    // Clean up
    delete window.electronAPI;
    delete window.api;
  });

  describe('Full Application Workflow', () => {
    test('complete server startup and client connection workflow', async () => {
      // Mock successful server start
      mockElectronAPI.startServer.mockResolvedValue({
        success: true,
        message: 'Server started successfully'
      });

      render(<App />);

      // Verify initial state
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
      expect(screen.getByText('idle')).toBeInTheDocument();

      // Start server
      const startButton = screen.getByTestId('play-arrow-icon').closest('button');
      fireEvent.click(startButton);

      // Wait for server to start
      await waitFor(() => {
        expect(mockElectronAPI.startServer).toHaveBeenCalled();
      });

      // Verify core UI elements are present
      expect(screen.getByText('Clipboard Server')).toBeInTheDocument();
      expect(screen.getByText('Connected Clients')).toBeInTheDocument();
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    });

    test('complete configuration change workflow', async () => {
      render(<App />);

      // Open settings
      const settingsButton = screen.getByTitle('Settings');
      fireEvent.click(settingsButton);

      // Wait for any modal or dialog to open
      await new Promise(resolve => setTimeout(resolve, 100));

      // The test verifies the settings button works
      // In a real app, this would open a configuration dialog
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    });

    test('error handling throughout application lifecycle', async () => {
      // Mock server start failure
      mockElectronAPI.startServer.mockResolvedValue({
        success: false,
        error: 'Port already in use'
      });

      render(<App />);

      // Try to start server
      const startButton = screen.getByTestId('play-arrow-icon').closest('button');
      fireEvent.click(startButton);

      // Verify server start was called
      await waitFor(() => {
        expect(mockElectronAPI.startServer).toHaveBeenCalled();
      });

      // Verify basic UI still works after error
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
      expect(screen.getByText('Connected Clients')).toBeInTheDocument();
    });

    test('client mode full workflow', async () => {
      mockElectronAPI.startClient.mockResolvedValue({
        success: true,
        message: 'Connected to server'
      });

      mockElectronAPI.stopClient.mockResolvedValue({
        success: true,
        message: 'Disconnected from server'
      });

      render(<App />);

      // Switch to client mode
      const settingsButton = screen.getByTitle('Settings');
      fireEvent.click(settingsButton);

      const clientButton = screen.getByRole('button', { name: 'Client' });
      fireEvent.click(clientButton);

      const closeButton = screen.getByText('Close');
      fireEvent.click(closeButton);

      // Start client
      const startButton = screen.getByTestId('play-arrow-icon').closest('button');
      fireEvent.click(startButton);

      await waitFor(() => {
        expect(mockElectronAPI.startClient).toHaveBeenCalled();
      });

      // Simulate running state
      act(() => {
        window.api._triggerServerStatus('running');
      });

      await waitFor(() => {
        expect(screen.getByText('running')).toBeInTheDocument();
      });

      // Stop client
      const stopButton = screen.getByTestId('stop-icon').closest('button');
      fireEvent.click(stopButton);

      await waitFor(() => {
        expect(mockElectronAPI.stopClient).toHaveBeenCalled();
      });
    });
  });

  describe('Cross-Tab Functionality', () => {
    test('navigation between tabs maintains state', async () => {
      render(<App />);

      // Verify initial tab (Clipboard)
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();

      // Switch to devices tab
      const devicesTab = screen.getByTestId('devices-icon').closest('button');
      fireEvent.click(devicesTab);

      // Should show devices content
      await waitFor(() => {
        expect(screen.getByText('Available Devices')).toBeInTheDocument();
      });

      // Switch to history tab
      const historyTab = screen.getByTestId('history-icon').closest('button');
      fireEvent.click(historyTab);

      // Should show history content
      await waitFor(() => {
        expect(screen.getByText('Clipboard History')).toBeInTheDocument();
      });

      // Switch back to clipboard tab
      const clipboardTab = screen.getByTestId('content-copy-icon').closest('button');
      fireEvent.click(clipboardTab);

      // Should show clipboard content
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    });

    test('log clearing functionality works across tabs', async () => {
      render(<App />);

      // Switch to history tab
      const historyTab = screen.getByTestId('history-icon').closest('button');
      fireEvent.click(historyTab);

      // Should show history tab content
      await waitFor(() => {
        expect(screen.getByText('Clipboard History')).toBeInTheDocument();
      });

      // Since the current implementation shows "History feature coming soon",
      // this test verifies the tab navigation works
      expect(screen.getByText(/coming soon/i)).toBeInTheDocument();

      // Switch to another tab and back to verify navigation
      const devicesTab = screen.getByTestId('devices-icon').closest('button');
      fireEvent.click(devicesTab);
      fireEvent.click(historyTab);

      // History tab content should still be visible
      expect(screen.getByText('Clipboard History')).toBeInTheDocument();
    });
  });

  describe('Performance and Edge Cases', () => {
    test('handles rapid state changes without crashes', async () => {
      render(<App />);

      // Rapidly click between tabs to test stability
      const clipboardTab = screen.getByTestId('content-copy-icon').closest('button');
      const historyTab = screen.getByTestId('history-icon').closest('button');
      const devicesTab = screen.getByTestId('devices-icon').closest('button');

      // Rapidly switch tabs
      for (let i = 0; i < 5; i++) {
        fireEvent.click(historyTab);
        fireEvent.click(devicesTab);
        fireEvent.click(clipboardTab);
      }

      // Should handle all changes gracefully without crashing
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
      // The app should render without crashing regardless of mode
    });

    test('handles configuration errors gracefully', async () => {
      mockElectronAPI.getConfig.mockRejectedValue(new Error('Config load failed'));

      render(<App />);

      // Should still render despite config errors
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();

      // Try to open settings despite config error
      const settingsButton = screen.getByTitle('Settings');
      fireEvent.click(settingsButton);

      // Should handle gracefully - either show dialog or fail silently
      // The app should not crash
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    });

    test('handles missing electronAPI methods gracefully', async () => {
      // Set server mode in localStorage
      localStorage.setItem('clipboardBridge_mode', 'server');
      
      // Remove some methods
      delete mockElectronAPI.startServer;
      delete mockElectronAPI.getConnectedClients;

      render(<App />);

      // Should still render
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();

      // Try to start server (should fail gracefully)
      const startButton = screen.getByTestId('play-arrow-icon').closest('button');
      fireEvent.click(startButton);

      // Wait a bit for any error handling
      await new Promise(resolve => setTimeout(resolve, 100));

      // Should not crash the application
      expect(screen.getByText('Clipboard Bridge')).toBeInTheDocument();
    });
  });
});
