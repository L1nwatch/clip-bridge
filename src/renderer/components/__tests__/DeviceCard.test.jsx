import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
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

describe('DeviceCard Component', () => {
  const defaultProps = {
    name: 'Test Device',
    ip: '192.168.1.100',
    status: 'connected'
  };

  test('renders device information correctly', () => {
    render(<DeviceCard {...defaultProps} />);
    
    expect(screen.getByText('Test Device')).toBeInTheDocument();
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  test('renders all required icons', () => {
    render(<DeviceCard {...defaultProps} />);
    
    expect(screen.getByTestId('grid-view-icon')).toBeInTheDocument();
    expect(screen.getByTestId('content-copy-icon')).toBeInTheDocument();
    expect(screen.getByTestId('content-paste-icon')).toBeInTheDocument();
  });

  test('displays correct status colors', () => {
    const { rerender } = render(<DeviceCard {...defaultProps} status="connected" />);
    let statusChip = screen.getByText('connected');
    expect(statusChip).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="disconnected" />);
    statusChip = screen.getByText('disconnected');
    expect(statusChip).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="connecting" />);
    statusChip = screen.getByText('connecting');
    expect(statusChip).toBeInTheDocument();

    rerender(<DeviceCard {...defaultProps} status="unknown" />);
    statusChip = screen.getByText('unknown');
    expect(statusChip).toBeInTheDocument();
  });

  test('action buttons are enabled when device is connected', () => {
    render(<DeviceCard {...defaultProps} status="connected" />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).not.toBeDisabled();
    expect(pasteButton).not.toBeDisabled();
  });

  test('action buttons are disabled when device is disconnected', () => {
    render(<DeviceCard {...defaultProps} status="disconnected" />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).toBeDisabled();
    expect(pasteButton).toBeDisabled();
  });

  test('action buttons are disabled when device is connecting', () => {
    render(<DeviceCard {...defaultProps} status="connecting" />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).toBeDisabled();
    expect(pasteButton).toBeDisabled();
  });

  test('action buttons are disabled for unknown status', () => {
    render(<DeviceCard {...defaultProps} status="unknown" />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).toBeDisabled();
    expect(pasteButton).toBeDisabled();
  });

  test('handles missing status prop with default value', () => {
    const propsWithoutStatus = {
      name: 'Test Device',
      ip: '192.168.1.100'
    };
    
    render(<DeviceCard {...propsWithoutStatus} />);
    
    expect(screen.getByText('unknown')).toBeInTheDocument();
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).toBeDisabled();
    expect(pasteButton).toBeDisabled();
  });

  test('button clicks work correctly', () => {
    render(<DeviceCard {...defaultProps} status="connected" />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    // Should not throw errors when clicked
    fireEvent.click(copyButton);
    fireEvent.click(pasteButton);
  });

  test('renders with long device names', () => {
    const longNameProps = {
      ...defaultProps,
      name: 'This is a very long device name that might cause layout issues'
    };
    
    render(<DeviceCard {...longNameProps} />);
    
    expect(screen.getByText(longNameProps.name)).toBeInTheDocument();
  });

  test('renders with IPv6 addresses', () => {
    const ipv6Props = {
      ...defaultProps,
      ip: '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
    };
    
    render(<DeviceCard {...ipv6Props} />);
    
    expect(screen.getByText(ipv6Props.ip)).toBeInTheDocument();
  });

  test('component has proper accessibility attributes', () => {
    render(<DeviceCard {...defaultProps} />);
    
    const copyButton = screen.getByLabelText('copy');
    const pasteButton = screen.getByLabelText('paste');
    
    expect(copyButton).toHaveAttribute('aria-label', 'copy');
    expect(pasteButton).toHaveAttribute('aria-label', 'paste');
  });
});
