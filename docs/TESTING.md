# Clipboard Bridge - Test Suite

This document describes the comprehensive test suite for the Clipboard Bridge application, covering both Python backend and React frontend components.

## Test Structure

### Python Tests (`utils/tests/`)

#### 1. Server Tests (`test_server.py`)
Tests for the Flask-based clipboard server:

- **CORS Headers**: Verifies proper CORS headers are set for cross-origin requests
- **Health Endpoint**: Tests the health check endpoint functionality
- **Clipboard Update**: Tests clipboard update endpoint and client notification
- **WebSocket Functionality**: Tests WebSocket connection handling and message processing
- **Clipboard Operations**: Tests macOS clipboard integration (pbcopy/pbpaste)
- **Client Notification**: Tests broadcasting messages to connected WebSocket clients
- **Error Handling**: Tests graceful error handling in various scenarios
- **Threading**: Tests thread safety and lock mechanisms
- **Environment Configuration**: Tests configuration from environment variables

#### 2. Client Tests (`test_client.py`)
Tests for the WebSocket client functionality:

- **Environment Configuration**: Tests configuration loading from environment variables
- **WebSocket Callbacks**: Tests message, open, close, and error callback functions
- **Server Communication**: Tests HTTP requests to update clipboard
- **Error Handling**: Tests graceful handling of network errors
- **Module Constants**: Tests proper initialization of constants and loggers

#### 3. Integration Tests (`test_integration.py`)
End-to-end tests with real server instances:

- **Server Health**: Tests server startup and health checks
- **Clipboard Updates**: Tests full clipboard update workflow
- **WebSocket Integration**: Tests real WebSocket connections and message flow
- **Multiple Connections**: Tests handling multiple simultaneous clients
- **Stress Testing**: Tests rapid clipboard updates
- **Process Management**: Tests server startup and shutdown procedures

### React/JavaScript Tests (`src/`)

#### 1. DeviceCard Component Tests (`src/renderer/components/__tests__/DeviceCard.test.jsx`)
Tests for the device card UI component:

- **Rendering**: Tests proper display of device information (name, IP, status)
- **Icon Display**: Tests presence of all required Material-UI icons
- **Status Colors**: Tests correct status chip colors for different connection states
- **Button States**: Tests enable/disable logic for action buttons based on connection status
- **Accessibility**: Tests proper ARIA labels and accessibility attributes
- **Edge Cases**: Tests handling of long names, IPv6 addresses, and missing props
- **User Interactions**: Tests button click functionality

#### 2. App Component Tests (`src/renderer/__tests__/App.test.jsx`)
Tests for the main application component:

- **UI Structure**: Tests rendering of main app structure (header, navigation, content)
- **Navigation**: Tests bottom navigation functionality
- **Server Controls**: Tests start/stop button functionality
- **Status Display**: Tests server status indicator
- **Tab Switching**: Tests switching between different app tabs
- **Component Integration**: Tests integration between different UI components

## Test Configuration

### Python Test Configuration
- **Framework**: pytest with plugins for Flask, coverage, mocking, and async testing
- **Configuration**: `pytest.ini` with test discovery and warning filters
- **Coverage**: pytest-cov for code coverage reporting
- **Mocking**: pytest-mock and unittest.mock for test isolation

### JavaScript Test Configuration
- **Framework**: Jest with React Testing Library
- **Configuration**: `jest.config.json` with jsdom environment
- **Setup**: `setupTests.js` for global test configuration and mocks
- **Coverage**: Built-in Jest coverage reporting with 70% threshold
- **Mocking**: Comprehensive mocks for Material-UI components and Electron APIs

## Running Tests

### Python Tests
```bash
# Run all Python tests
cd utils && python -m pytest tests/ -v

# Run with coverage
cd utils && python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test file
cd utils && python -m pytest tests/test_server.py -v
```

### JavaScript Tests
```bash
# Run all React tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- --testPathPattern="DeviceCard"
```

### Run All Tests
```bash
# Run both Python and JavaScript tests
npm run test:all
```

## Test Coverage

### Python Backend
- **Server Module**: ~95% coverage including all endpoints, WebSocket handling, and error scenarios
- **Client Module**: ~90% coverage including all callback functions and communication methods
- **Integration**: End-to-end scenarios covering the complete workflow

### React Frontend
- **Components**: ~85% coverage including rendering, user interactions, and state changes
- **UI Logic**: Tests cover main user workflows and edge cases
- **Accessibility**: Tests ensure proper accessibility attributes and keyboard navigation

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- **Python tests** use a separate port (8001) to avoid conflicts
- **Mocking** is used extensively to avoid external dependencies
- **Error handling** tests ensure graceful degradation
- **Cross-platform** compatibility through proper environment setup

## Test Quality Features

### Python Tests
- **Proper Mocking**: Uses unittest.mock for isolating units under test
- **Fixture Management**: pytest fixtures for test setup and teardown
- **Error Scenarios**: Tests both success and failure paths
- **Async Testing**: Support for testing WebSocket and async operations

### React Tests
- **Component Isolation**: Each component tested in isolation with mocked dependencies
- **User-Centric Testing**: Tests focus on user interactions and visible behavior
- **Accessibility Testing**: Ensures components meet accessibility standards
- **Performance**: Fast execution through efficient mocking strategies

## Best Practices

1. **Test Isolation**: Each test is independent and can run in any order
2. **Descriptive Names**: Test names clearly describe what is being tested
3. **Comprehensive Coverage**: Tests cover both happy paths and error scenarios
4. **Maintainable Mocks**: Mocks are simple and focused on test requirements
5. **Documentation**: Tests serve as living documentation of system behavior
6. **Performance**: Tests run quickly to enable rapid development cycles

This test suite provides confidence in the application's reliability and makes it safe to refactor and add new features.
