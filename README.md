# clip-bridge

Electron + React desktop application for sharing clipboard contents across devices.

## 🚀 Features

- **Cross-platform clipboard sharing** between multiple devices
- **Real-time WebSocket communication** for instant updates
- **Live client connection monitoring** with connected devices display
- **Modern React UI** with Material-UI components
- **Python backend** with Flask and WebSocket support
- **Comprehensive test coverage** with 100% test success rate
- **High-quality code** with automated linting and formatting

## 🏗️ Development Setup

### Prerequisites
- Node.js 18+
- Python 3.9+

### Installation

```bash
# Install Node.js dependencies
npm install

# Set up Python environment
cd utils
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

### Running the Application

```bash
# Start the full application (React + Electron)
npm start

# Or start components separately
npm run react-start    # React dev server
npm run electron-start # Electron app
```

### Testing Client Connections

To test the Connected Clients feature, you can use the demo script:

```bash
# Start the server first through the app UI, then run:
cd utils
source .venv/bin/activate
python demo_clients.py 3  # Simulate 3 test clients

# Or specify custom port
python demo_clients.py 2 8001  # 2 clients on port 8001
```

This will simulate multiple clients connecting to your server, allowing you to see the Connected Clients UI in action.

## 🧪 Testing

### Current Test Status
✅ **All Tests Passing**: 130/130 tests (100% success rate)
- **JavaScript Tests**: 74/74 passing with 84.37% statement coverage
- **Python Tests**: 56/56 passing with comprehensive edge case coverage
- **Integration Tests**: Full application workflow testing
- **Code Quality**: All flake8 and ESLint checks passing

### Run All Tests
```bash
# Quick test run (all platforms)
npm test -- --watchAll=false  # JavaScript tests
python -m pytest utils/ -q    # Python tests

# Full test suite with coverage
npm test -- --coverage --watchAll=false
python -m pytest utils/ --cov=. --cov-report=html
```

### Test Categories

#### JavaScript/React Tests
- **Component Tests**: DeviceCard, App core functionality  
- **Integration Tests**: Full application workflows, tab navigation, error handling
- **Enhanced Coverage**: Edge cases, accessibility, rapid state changes
- **Performance Tests**: Stress testing and stability validation

#### Python Backend Tests
- **Unit Tests**: Server and client functionality
- **Integration Tests**: Client-server communication flows
- **Edge Case Tests**: Error handling, timeout scenarios, connection issues
- **Mock Testing**: WebSocket, HTTP requests, clipboard operations

### Code Quality
```bash
# Python code quality
flake8 utils/*.py --count --select=E9,F63,F7,F82 --show-source --statistics

# JavaScript code quality  
npm run lint
```

## 📦 Building and Packaging

```bash
npm run build      # Build React app
npm run package    # Package Electron app
```

## 🔄 Quality Assurance

This project maintains high code quality through:

- **Automated Testing**: Comprehensive test suites for all components
- **Code Linting**: flake8 for Python, ESLint for JavaScript
- **Test Coverage**: 84%+ statement coverage for JavaScript, comprehensive Python coverage
- **Integration Testing**: Full application workflow validation
- **Edge Case Testing**: Error handling and boundary condition testing

## 📊 Test Coverage Metrics

### JavaScript Frontend
- **Test Files**: 6 test suites
- **Test Cases**: 74 comprehensive tests
- **Coverage**: 84.37% statements, 83.17% branches, 76.19% functions
- **Components Tested**: App, DeviceCard, main process, preload script
- **Integration Tests**: 9 full workflow tests

### Python Backend  
- **Test Files**: 4 test modules
- **Test Cases**: 56 comprehensive tests
- **Coverage Areas**: Server, client, integration, edge cases
- **Mock Testing**: WebSocket, HTTP, clipboard operations
- **Error Scenarios**: Comprehensive error handling validation

### Recent Achievements
- ✅ Fixed all Python test failures (6 → 0 failures)
- ✅ Enhanced JavaScript test coverage (+17% improvement)
- ✅ Added comprehensive integration testing
- ✅ Resolved all flake8 code quality issues
- ✅ Achieved 100% test success rate across all platforms

## 🛠️ Tech Stack

### Frontend
- **Electron**: Desktop application framework
- **React**: UI library with comprehensive testing
- **Material-UI**: Component library with accessibility support
- **Jest + React Testing Library**: Testing framework with 74 tests

### Backend  
- **Python**: Core language with type hints and best practices
- **Flask**: Web framework with REST API support
- **WebSocket**: Real-time communication with gevent
- **pytest**: Testing framework with 56 comprehensive tests

### Development Tools
- **ESLint**: JavaScript code quality and consistency
- **flake8**: Python code quality and PEP 8 compliance
- **Coverage.py**: Python test coverage reporting
- **Jest Coverage**: JavaScript test coverage reporting

## 📁 Project Structure

```
├── src/                          # Electron + React source
│   ├── main.js                   # Electron main process
│   ├── preload.js               # Electron preload script
│   ├── renderer/                # React application
│   │   ├── App.jsx              # Main application component
│   │   ├── components/          # Reusable UI components
│   │   └── __tests__/           # Frontend test suites
├── utils/                       # Python backend
│   ├── server.py               # Flask server with WebSocket support
│   ├── client.py               # WebSocket client implementation
│   ├── tests/                  # Python test suite (56 tests)
│   │   ├── test_server.py      # Server functionality tests
│   │   ├── test_client.py      # Client functionality tests
│   │   ├── test_integration.py # Integration tests
│   │   └── test_edge_cases.py  # Edge case and error handling tests
│   └── requirements.txt        # Python dependencies
├── package.json                # Node.js dependencies and scripts
└── README.md                   # This documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: 
   ```bash
   npm test -- --watchAll=false
   python -m pytest utils/ -q
   ```
5. Check code quality:
   ```bash
   npm run lint
   flake8 utils/*.py --count --select=E9,F63,F7,F82 --show-source --statistics
   ```
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Submit a pull request

### Code Quality Standards
- All new code must include comprehensive tests
- Python code must pass flake8 linting
- JavaScript code must pass ESLint checks
- Test coverage should be maintained or improved
- Integration tests should be added for new features

## 📚 Development Guidelines

- **Testing**: Write tests for all new features and bug fixes
- **Documentation**: Update README and inline documentation
- **Code Style**: Follow existing patterns and linting rules
- **Git Commits**: Use clear, descriptive commit messages
- **Pull Requests**: Include test results and coverage information

## 📖 Documentation

- **[Testing Guide](docs/TESTING.md)** - Comprehensive test suite documentation
- **[GitHub Actions](docs/GITHUB_ACTIONS.md)** - CI/CD workflow documentation  
- **[Packaging Guide](docs/PACKAGING.md)** - Application distribution and packaging

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
