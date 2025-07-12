import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';

// Mock the localStorage to test settings persistence
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock window.api
const mockAPI = {
  startServer: jest.fn().mockResolvedValue({ success: true }),
  stopServer: jest.fn().mockResolvedValue({ success: true }),
  startClient: jest.fn().mockResolvedValue({ success: true }),
  stopClient: jest.fn().mockResolvedValue({ success: true }),
  onServerLog: jest.fn(),
  onClientLog: jest.fn(),
  onServerStatus: jest.fn(),
  onClientStatus: jest.fn(),
  onClientConnected: jest.fn(),
  onClientDisconnected: jest.fn(),
  getServiceStatus: jest.fn().mockResolvedValue({ server: 'stopped', client: 'stopped' }),
  getConnectedClients: jest.fn().mockResolvedValue([]),
};

Object.defineProperty(window, 'api', {
  value: mockAPI,
  writable: true,
});

describe('Settings Persistence', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.clear.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
  });

  test('loads default settings when localStorage is empty', () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    // Should start in default server mode
    expect(screen.getByText('Clipboard Server')).toBeInTheDocument();
    expect(localStorageMock.getItem).toHaveBeenCalledWith('clipBridgeSettings');
  });

  test('loads saved settings from localStorage', () => {
    const savedSettings = {
      mode: 'client',
      config: {
        port: 9000,
        serverAddress: '192.168.1.100',
        autoStart: true,
        logLevel: 'DEBUG'
      }
    };
    localStorageMock.getItem.mockReturnValue(JSON.stringify(savedSettings));
    
    render(<App />);
    
    // Should start in client mode with saved settings
    expect(screen.getByText('Clipboard Client')).toBeInTheDocument();
    expect(screen.getByText('Connecting to 192.168.1.100:9000')).toBeInTheDocument();
    expect(localStorageMock.getItem).toHaveBeenCalledWith('clipBridgeSettings');
  });

  test('saves settings to localStorage when mode changes', async () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    // Open settings dialog
    const settingsButton = screen.getByTitle('Settings');
    fireEvent.click(settingsButton);
    
    // Switch to client mode
    const clientButton = screen.getByText('Client');
    fireEvent.click(clientButton);
    
    // Close settings dialog
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    // Should have saved the new mode to localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'clipBridgeSettings',
      expect.stringContaining('"mode":"client"')
    );
  });

  test('saves settings when config changes', async () => {
    localStorageMock.getItem.mockReturnValue(null);
    
    render(<App />);
    
    // Open settings dialog
    const settingsButton = screen.getByTitle('Settings');
    fireEvent.click(settingsButton);
    
    // Change port
    const portInput = screen.getByLabelText('Port');
    fireEvent.change(portInput, { target: { value: '9000' } });
    
    // Should have saved the new config to localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'clipBridgeSettings',
      expect.stringContaining('"port":9000')
    );
  });

  test('handles corrupted localStorage data gracefully', () => {
    localStorageMock.getItem.mockReturnValue('invalid json');
    
    // Should not throw error and use default settings
    expect(() => render(<App />)).not.toThrow();
    expect(screen.getByText('Clipboard Server')).toBeInTheDocument();
  });
});
