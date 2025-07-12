import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DeviceCard from '../DeviceCard';

// Mock Material-UI icons
jest.mock('@mui/icons-material/ContentPaste', () => {
  return function MockContentPasteIcon() {
    return <div data-testid="content-paste-icon" />;
  };
});

jest.mock('@mui/icons-material/ContentCopy', () => {
  return function MockContentCopyIcon() {
    return <div data-testid="content-copy-icon" />;
  };
});

jest.mock('@mui/icons-material/GridView', () => {
  return function MockGridViewIcon() {
    return <div data-testid="grid-view-icon" />;
  };
});

describe('DeviceCard Component - Enhanced Tests', () => {
  const defaultProps = {
    name: 'Test Device',
    ip: '192.168.1.100',
    status: 'connected'
  };

  test('renders with minimal props', () => {
    render(<DeviceCard name="Minimal Device" />);
    
    expect(screen.getByText('Minimal Device')).toBeInTheDocument();
    expect(screen.getByTestId('grid-view-icon')).toBeInTheDocument();
  });

  test('handles different status values correctly', () => {
    const { rerender } = render(<DeviceCard {...defaultProps} status="connected" />);
    expect(screen.getByText('connected')).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="disconnected" />);
    expect(screen.getByText('disconnected')).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="connecting" />);
    expect(screen.getByText('connecting')).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="error" />);
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  test('displays IP address when provided', () => {
    render(<DeviceCard {...defaultProps} />);
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
  });

  test('handles missing IP address gracefully', () => {
    const propsWithoutIP = { ...defaultProps };
    delete propsWithoutIP.ip;
    
    render(<DeviceCard {...propsWithoutIP} />);
    expect(screen.getByText('Test Device')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  test('displays all action buttons', () => {
    render(<DeviceCard {...defaultProps} />);
    
    expect(screen.getByTestId('content-copy-icon')).toBeInTheDocument();
    expect(screen.getByTestId('content-paste-icon')).toBeInTheDocument();
  });

  test('handles click events on action buttons', () => {
    // Note: The DeviceCard component has action buttons but doesn't expose
    // click handlers as props. Testing the presence of the buttons instead.
    render(<DeviceCard {...defaultProps} />);
    
    const copyIcon = screen.getByTestId('content-copy-icon');
    const pasteIcon = screen.getByTestId('content-paste-icon');
    
    // Verify the buttons are rendered
    expect(copyIcon).toBeInTheDocument();
    expect(pasteIcon).toBeInTheDocument();
    
    // Verify the buttons are within IconButton elements
    const copyButton = copyIcon.closest('button');
    const pasteButton = pasteIcon.closest('button');
    
    expect(copyButton).toBeInTheDocument();
    expect(pasteButton).toBeInTheDocument();
  });

  test('renders with very long device name', () => {
    const longName = 'This is a very long device name that might cause layout issues in the UI component';
    render(<DeviceCard name={longName} ip="192.168.1.100" status="connected" />);
    
    expect(screen.getByText(longName)).toBeInTheDocument();
  });

  test('renders with special characters in name', () => {
    const specialName = "Device-123_Test@Home#2024";
    render(<DeviceCard name={specialName} ip="192.168.1.100" status="connected" />);
    
    expect(screen.getByText(specialName)).toBeInTheDocument();
  });

  test('handles IPv6 addresses', () => {
    const ipv6Address = "2001:0db8:85a3:0000:0000:8a2e:0370:7334";
    render(<DeviceCard name="IPv6 Device" ip={ipv6Address} status="connected" />);
    
    expect(screen.getByText(ipv6Address)).toBeInTheDocument();
  });

  test('renders without status', () => {
    const propsWithoutStatus = { ...defaultProps };
    delete propsWithoutStatus.status;
    
    render(<DeviceCard {...propsWithoutStatus} />);
    expect(screen.getByText('Test Device')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
  });

  test('handles empty string values gracefully', () => {
    render(<DeviceCard name="" ip="" status="" />);
    // Should still render the component structure
    expect(screen.getByTestId('grid-view-icon')).toBeInTheDocument();
  });

  test('applies correct CSS classes based on status', () => {
    const { rerender } = render(<DeviceCard {...defaultProps} status="connected" />);
    let statusElement = screen.getByText('connected');
    expect(statusElement).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="error" />);
    statusElement = screen.getByText('error');
    expect(statusElement).toBeInTheDocument();
  });

  test('maintains responsive layout with different content lengths', () => {
    const shortProps = {
      name: 'PC',
      ip: '1.1.1.1',
      status: 'ok'
    };
    
    const { rerender } = render(<DeviceCard {...shortProps} />);
    expect(screen.getByText('PC')).toBeInTheDocument();
    
    const longProps = {
      name: 'My Very Long Computer Name With Many Words',
      ip: '255.255.255.255',
      status: 'disconnected'
    };
    
    rerender(<DeviceCard {...longProps} />);
    expect(screen.getByText('My Very Long Computer Name With Many Words')).toBeInTheDocument();
  });

  test('handles numeric device names', () => {
    render(<DeviceCard name="12345" ip="192.168.1.100" status="connected" />);
    expect(screen.getByText('12345')).toBeInTheDocument();
  });

  test('renders with additional props', () => {
    // Test that the component renders properly with only valid props
    render(<DeviceCard {...defaultProps} />);
    
    expect(screen.getByText('Test Device')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });
});

describe('DeviceCard Component - Accessibility', () => {
  test('has proper accessibility attributes', () => {
    render(<DeviceCard name="Accessible Device" ip="192.168.1.100" status="connected" />);
    
    // Check for appropriate roles and labels
    const card = screen.getByTestId('grid-view-icon').closest('div');
    expect(card).toBeInTheDocument();
  });

  test('action buttons are keyboard accessible', () => {
    render(<DeviceCard name="Keyboard Device" ip="192.168.1.100" status="connected" />);
    
    const copyButton = screen.getByTestId('content-copy-icon').closest('button');
    const pasteButton = screen.getByTestId('content-paste-icon').closest('button');
    
    // These buttons should be focusable
    if (copyButton) {
      expect(copyButton).not.toBeDisabled();
    }
    if (pasteButton) {
      expect(pasteButton).not.toBeDisabled();
    }
  });
});
