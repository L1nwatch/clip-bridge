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
- **Native Windows/macOS executables** via GitHub Actions CI/CD

## 📦 Building for Windows

### Option 1: Download Pre-built Executables (Recommended)

The project uses GitHub Actions to build native Windows x64 executables:

```bash
# Download latest Windows executables using GitHub CLI
./scripts/download-windows-executables.sh

# Then build the Windows installer
./scripts/build-win11.sh
```

### Option 2: Automated Download in Build Script

The Windows build script automatically tries to download pre-built executables:

```bash
# This will automatically download Windows executables if available
./scripts/build-win11.sh
```

### Option 3: Manual Download from Releases

1. Go to the [Releases page](https://github.com/L1nwatch/clip-bridge/releases)
2. Download `clipbridge-windows-x64.zip`
3. Extract to `dist/python-standalone/`
4. Run `./scripts/build-win11.sh`

### Why GitHub Actions?

- **True Windows compatibility**: Built on Windows runners, not cross-compiled
- **Proper x64 architecture**: Native Windows x64 executables  
- **No compatibility errors**: Eliminates "not compatible with Windows" issues
- **Automated builds**: Fresh executables with every code change

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

### Troubleshooting

#### "Cannot find module 'build/electron.js'" Error
If you encounter this error when starting the app:
```bash
# First, build the project to create the build directory
npm run build

# Then start the application
npm start
```

The build process creates the necessary `build/electron.js` file that Electron needs for production builds.

#### "Failed to send clipboard to Mac (Status: 407)" Error
This error indicates a proxy authentication issue. Try these solutions:

1. **Disable proxy for local connections:**
   ```bash
   # On Windows, temporarily disable proxy
   # Go to Settings > Network & Internet > Proxy > Turn off "Use a proxy server"
   ```

2. **Check network connectivity:**
   ```bash
   # Test if the Mac server is reachable
   curl http://[MAC_IP]:8000/
   
   # Or use telnet to test the port
   telnet [MAC_IP] 8000
   ```

3. **Firewall issues:**
   - Make sure port 8000 is open on both devices
   - Check if Windows Firewall or Mac Firewall is blocking the connection
   - Try running on a different port: `PORT=8001 python server.py`

4. **Network configuration:**
   - Ensure both devices are on the same network
   - Check if VPN is interfering with local connections
   - Try using the Mac's IP address instead of 'localhost'

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
# Clean build React app
npm run build:clean   # Clean previous builds and rebuild

# Build distribution packages (outputs only .dmg and .exe files)
npm run dist:mac      # Build ARM64 DMG for macOS (Apple Silicon)
npm run dist:win11    # Build x64 EXE for Windows
npm run dist:official # Build both platforms with cleanup

# Manual cleanup commands
npm run clean:temp      # Remove temporary build files
npm run clean:artifacts # Keep only .dmg and .exe files in dist/electron/
```

### Distribution Output
After building, you'll find only these files in `dist/electron/`:
- **`ClipBridge-0.1.0-arm64.dmg`** - macOS installer for Apple Silicon
- **`ClipBridge Setup 0.1.0.exe`** - Windows installer for x64

All other build artifacts (directories, config files, block maps) are automatically removed.

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
- ✅ Streamlined build process with automatic cleanup
- ✅ Optimized for Apple Silicon (ARM64) and Windows x64

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
├── config/                      # Configuration files
│   ├── electron-builder.json   # Electron packaging configuration
│   ├── eslint.config.mjs       # ESLint rules and settings
│   ├── jsconfig.json           # JavaScript/TypeScript project settings
│   ├── jest.config.json        # Jest testing framework configuration
│   └── pyproject.toml          # Python project configuration
├── scripts/                     # Build and automation scripts
├── package.json                # Node.js dependencies and scripts
├── jsconfig.json               # → config/jsconfig.json (symlink)
├── eslint.config.mjs           # → config/eslint.config.mjs (symlink)
└── README.md                   # This documentation
```

> **Note**: Some config files (jsconfig.json, eslint.config.mjs) have symlinks in the root directory for tool compatibility, but the actual files are organized in the `config/` folder.

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
