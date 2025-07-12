# clip-bridge

Electron + React desktop application for sharing clipboard contents across devices.

## 🚀 Features

- **Cross-platform clipboard sharing** between multiple devices
- **Real-time WebSocket communication** for instant updates
- **Live client connection monitoring** with connected devices display
- **Modern React UI** with Material-UI components
- **Python backend** with Flask and WebSocket support
- **Comprehensive test coverage** for both frontend and backend

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

### Run All Tests
```bash
npm run test:all        # Both Python and React tests
```

### Python Tests
```bash
npm run test:python             # Run pytest
npm run test:python:coverage    # With coverage report
```

### React Tests
```bash
npm run test:coverage   # React tests with coverage
npm test               # Interactive test runner
```

### Pre-commit Validation
```bash
# Run the full CI validation locally
./scripts/validate-ci.sh
```

## 📦 Building and Packaging

```bash
npm run build      # Build React app
npm run package    # Package Electron app
```

## 🔄 Continuous Integration

This project uses GitHub Actions for automated testing and quality assurance:

- **Python Tests**: pytest across Python 3.9, 3.10, 3.11
- **React Tests**: Jest with React Testing Library
- **Code Quality**: Black, flake8, ESLint
- **Coverage**: Comprehensive coverage reporting
- **Integration**: End-to-end system testing

See [GITHUB_ACTIONS.md](./GITHUB_ACTIONS.md) for detailed CI/CD documentation.

## 📊 Test Coverage

- **Python Backend**: 36 tests covering server, client, and integration
- **React Frontend**: 17 tests covering components and user interactions
- **Total**: 53 comprehensive tests with coverage reporting

## 🛠️ Tech Stack

### Frontend
- **Electron**: Desktop application framework
- **React**: UI library
- **Material-UI**: Component library
- **Jest**: Testing framework

### Backend  
- **Python**: Core language
- **Flask**: Web framework
- **WebSocket**: Real-time communication
- **pytest**: Testing framework

## 📁 Project Structure

```
├── src/                          # Electron + React source
│   ├── main.js                   # Electron main process
│   ├── preload.js               # Electron preload script
│   └── renderer/                # React application
├── utils/                       # Python backend
│   ├── server.py               # Flask server
│   ├── client.py               # WebSocket client
│   └── tests/                  # Python test suite
├── .github/workflows/          # CI/CD workflows
└── scripts/                    # Development tools
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `./scripts/validate-ci.sh`
4. Submit a pull request

All pull requests must pass the CI pipeline including:
- All tests passing
- Code formatting compliance
- Coverage requirements met

## � Documentation

- **[Testing Guide](docs/TESTING.md)** - Comprehensive test suite documentation
- **[GitHub Actions](docs/GITHUB_ACTIONS.md)** - CI/CD workflow documentation  
- **[Packaging Guide](docs/PACKAGING.md)** - Application distribution and packaging

## �📄 License

[Add your license here]
