# GitHub Actions CI/CD Workflow

This repository uses GitHub Actions for continuous integration and testing.

## Workflow Overview

The CI workflow (`.github/workflows/ci.yml`) runs automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** targeting `main` or `develop` branches

## Jobs

### 1. Python Tests (`test`)
- **Runs on**: Ubuntu Latest
- **Python versions**: 3.9, 3.10, 3.11 (matrix strategy)
- **Steps**:
  - Install Python dependencies from `utils/requirements.txt`
  - Run the comprehensive test suite (`test_clipboard_bridge.py`)
  - Upload test results as artifacts (retained for 30 days)

### 2. Code Linting (`lint`)
- **Runs on**: Ubuntu Latest
- **Python version**: 3.9
- **Steps**:
  - Check code formatting with Black
  - Lint Python code with flake8
  - Check for syntax errors and code quality issues

### 3. Electron App Tests (`electron-test`)
- **Runs on**: Ubuntu Latest
- **Node.js version**: 18
- **Steps**:
  - Install Node.js dependencies
  - Run ESLint on JavaScript/React code
  - Build the Electron application

## Running Tests Locally

### Python Tests
```bash
cd utils
python test_clipboard_bridge.py
```

### JavaScript/React Linting
```bash
npm run lint
```

### Code Formatting
```bash
# Check formatting
black --check utils/

# Fix formatting
black utils/
```

## Status Badges

You can add these badges to your main README.md:

```markdown
![CI Tests](https://github.com/L1nwatch/clip-bridge/workflows/CI%20Tests/badge.svg)
```

## Troubleshooting

- **Python tests failing**: Check that all dependencies in `requirements.txt` are correct
- **Linting errors**: Run `black utils/` to auto-format Python code
- **Electron build failing**: Ensure all Node.js dependencies are properly installed

## Customization

To modify the workflow:
1. Edit `.github/workflows/ci.yml`
2. Adjust Python versions in the matrix strategy
3. Add or remove linting rules
4. Modify test commands as needed
