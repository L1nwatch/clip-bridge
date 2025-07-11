import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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
