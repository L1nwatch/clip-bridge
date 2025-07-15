const { app, BrowserWindow, ipcMain, clipboard } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const isDev = process.env.NODE_ENV === 'development';

let serverProcess = null;
let clientProcess = null;
let connectedClients = new Map(); // Track connected clients: clientId -> clientInfo

// Helper functions for Python executable paths
function getPythonExecutablePath() {
  if (isDev) {
    // In development, use Python from virtual environment
    return process.platform === 'win32' ? 'python' : 'python3';
  } else {
    // In production, check if we have standalone executables
    // Try multiple possible resource paths in case the default one isn't available
    const possibleResourcePaths = [
      process.resourcesPath,
      path.join(process.execPath, '..', 'resources'),
      path.join(path.dirname(process.execPath), 'resources'),
      path.join(app.getAppPath(), '..', 'resources'),
      path.join(app.getPath('exe'), '..', 'resources')
    ];
    
    console.log('Checking possible resource paths:');
    possibleResourcePaths.forEach(resPath => {
      console.log(`- ${resPath} (exists: ${fs.existsSync(resPath)})`);
    });
    
    // Find the first valid resources path
    let resourcesPath = null;
    for (const resPath of possibleResourcePaths) {
      if (fs.existsSync(resPath)) {
        resourcesPath = resPath;
        console.log('Using resources path:', resourcesPath);
        break;
      }
    }
    
    if (!resourcesPath) {
      console.error('No valid resources path found, using default');
      resourcesPath = process.resourcesPath;
    }
    
    // Try both with and without .exe extension to support cross-platform builds
    const possibleExecutables = [
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server.exe'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server.bat'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server-win.py'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server.py')
    ];
    
    // For Windows, prioritize Python scripts and .bat files over potentially incompatible .exe files
    if (process.platform === 'win32') {
      possibleExecutables.sort((a, b) => {
        if (a.endsWith('-win.py') && !b.endsWith('-win.py')) return -1;
        if (!a.endsWith('-win.py') && b.endsWith('-win.py')) return 1;
        if (a.endsWith('.py') && !b.endsWith('.py')) return -1;
        if (!a.endsWith('.py') && b.endsWith('.py')) return 1;
        if (a.endsWith('.bat') && !b.endsWith('.bat')) return -1;
        if (!a.endsWith('.bat') && b.endsWith('.bat')) return 1;
        if (a.endsWith('.exe') && !b.endsWith('.exe')) return -1;
        if (!a.endsWith('.exe') && b.endsWith('.exe')) return 1;
        return 0;
      });
    }
    
    // Log all possible paths we're checking
    possibleExecutables.forEach(execPath => {
      console.log(`Checking executable path: ${execPath} (exists: ${fs.existsSync(execPath)})`);
    });
    
    let standaloneServer = null;
    
    // Find the first executable that exists
    for (const execPath of possibleExecutables) {
      console.log('Checking for standalone executable at:', execPath);
      if (fs.existsSync(execPath)) {
        standaloneServer = execPath;
        break;
      }
    }
    
    if (!standaloneServer) {
      // Default to platform-specific path for error messages
      standaloneServer = process.platform === 'win32' 
        ? path.join(resourcesPath, 'python-standalone', 'clipbridge-server.exe')
        : path.join(resourcesPath, 'python-standalone', 'clipbridge-server');
    }
    
    console.log('Selected standalone executable:', standaloneServer);
    
    // List all files in the directory to debug
    try {
      const dir = path.dirname(standaloneServer);
      if (fs.existsSync(dir)) {
        console.log('Contents of python-standalone directory:');
        const files = fs.readdirSync(dir);
        files.forEach(file => {
          console.log('  -', file);
        });
      } else {
        console.log('python-standalone directory does not exist:', dir);
      }
    } catch (err) {
      console.error('Error listing directory:', err);
    }
    
    // If the standalone executable exists, we'll use it directly (returning null)
    // Our startServer function will handle this special case
    if (fs.existsSync(standaloneServer)) {
      console.log('Using standalone Python executable:', standaloneServer);
      return null; // Special marker that we're using standalone exe
    } else {
      // Fallback to system Python if standalone not available
      console.log('Standalone executable not found, falling back to system Python');
      return process.platform === 'win32' ? 'python' : 'python3';
    }
  }
}

function getPythonScriptPath() {
  if (isDev) {
    // In development, use the actual Python files
    return path.join(__dirname, '..', 'utils', 'server.py');
  } else {
    // Try multiple possible resource paths in case the default one isn't available
    const possibleResourcePaths = [
      process.resourcesPath,
      path.join(process.execPath, '..', 'resources'),
      path.join(path.dirname(process.execPath), 'resources'),
      path.join(app.getAppPath(), '..', 'resources'),
      path.join(app.getPath('exe'), '..', 'resources')
    ];
    
    // Find the first valid resources path
    let resourcesPath = null;
    for (const resPath of possibleResourcePaths) {
      if (fs.existsSync(resPath)) {
        resourcesPath = resPath;
        console.log('Using resources path for server script:', resourcesPath);
        break;
      }
    }
    
    if (!resourcesPath) {
      console.error('No valid resources path found for server script, using default');
      resourcesPath = process.resourcesPath;
    }
    
    // Try both with and without .exe extension to support cross-platform builds
    const possibleExecutables = [
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server.exe'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-server.bat')
    ];
    
    // Find the first executable that exists
    for (const execPath of possibleExecutables) {
      if (fs.existsSync(execPath)) {
        console.log('Found server executable at:', execPath);
        return execPath; // Return the path to the standalone executable
      }
    }
    
    // Default to platform-specific path for error messages
    const standaloneServer = process.platform === 'win32' 
      ? path.join(resourcesPath, 'python-standalone', 'clipbridge-server.exe')
      : path.join(resourcesPath, 'python-standalone', 'clipbridge-server');
      
    // Log error instead of falling back
    console.error('Standalone server executable not found. This is required for operation.');
    return standaloneServer; // Return the path anyway, will fail gracefully later with a clear error
  }
}

function getClientScriptPath() {
  if (isDev) {
    return path.join(__dirname, '..', 'utils', 'client.py');
  } else {
    // Try multiple possible resource paths in case the default one isn't available
    const possibleResourcePaths = [
      process.resourcesPath,
      path.join(process.execPath, '..', 'resources'),
      path.join(path.dirname(process.execPath), 'resources'),
      path.join(app.getAppPath(), '..', 'resources'),
      path.join(app.getPath('exe'), '..', 'resources')
    ];
    
    // Find the first valid resources path
    let resourcesPath = null;
    for (const resPath of possibleResourcePaths) {
      if (fs.existsSync(resPath)) {
        resourcesPath = resPath;
        console.log('Using resources path for client script:', resourcesPath);
        break;
      }
    }
    
    if (!resourcesPath) {
      console.error('No valid resources path found for client script, using default');
      resourcesPath = process.resourcesPath;
    }
    
    // Try both with and without .exe extension to support cross-platform builds
    const possibleExecutables = [
      path.join(resourcesPath, 'python-standalone', 'clipbridge-client.exe'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-client'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-client.bat'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-client-win.py'),
      path.join(resourcesPath, 'python-standalone', 'clipbridge-client.py')
    ];
    
    // For Windows, prioritize Python scripts and .bat files over potentially incompatible .exe files
    if (process.platform === 'win32') {
      possibleExecutables.sort((a, b) => {
        if (a.endsWith('-win.py') && !b.endsWith('-win.py')) return -1;
        if (!a.endsWith('-win.py') && b.endsWith('-win.py')) return 1;
        if (a.endsWith('.py') && !b.endsWith('.py')) return -1;
        if (!a.endsWith('.py') && b.endsWith('.py')) return 1;
        if (a.endsWith('.bat') && !b.endsWith('.bat')) return -1;
        if (!a.endsWith('.bat') && b.endsWith('.bat')) return 1;
        if (a.endsWith('.exe') && !b.endsWith('.exe')) return -1;
        if (!a.endsWith('.exe') && b.endsWith('.exe')) return 1;
        return 0;
      });
    }
    
    // Log all possible paths we're checking
    possibleExecutables.forEach(execPath => {
      console.log(`Checking client executable path: ${execPath} (exists: ${fs.existsSync(execPath)})`);
    });
    
    // Find the first executable that exists
    for (const execPath of possibleExecutables) {
      if (fs.existsSync(execPath)) {
        console.log('Found client executable at:', execPath);
        return execPath; // Return the path to the standalone executable
      }
    }
    
    // Default to platform-specific path for error messages
    const standaloneClient = process.platform === 'win32' 
      ? path.join(resourcesPath, 'python-standalone', 'clipbridge-client.exe')
      : path.join(resourcesPath, 'python-standalone', 'clipbridge-client');
      
    // Log error instead of falling back
    console.error('Standalone client executable not found. This is required for operation.');
    console.error('Looked for executables at:');
    possibleExecutables.forEach(path => console.error(`- ${path}`));
    return standaloneClient; // Return the path anyway, will fail gracefully later with a clear error
  }
}

function createWindow() {
  const win = new BrowserWindow({
    width: 540,
    height: 835,
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
    show: false, // Don't show until ready
  });

  // Disable menu bar
  win.setMenuBarVisibility(false);

  // Show window when ready to prevent visual flash
  win.once('ready-to-show', () => {
    win.show();
  });

  // Inject CSS to prevent scrolling at the webContents level
  win.webContents.on('dom-ready', () => {
    win.webContents.insertCSS(`
      html, body {
        overflow: hidden !important;
        height: 100vh !important;
      }
      ::-webkit-scrollbar {
        display: none !important;
      }
    `);
  });

  if (isDev) {
    const reactPort = process.env.PORT || '3000';
    const reactUrl = `http://localhost:${reactPort}`;
    
    win.loadURL(reactUrl).catch(err => {
      console.error(`Failed to load development URL (${reactUrl}):`, err);
      // Fallback to file if dev server is not ready
      win.loadFile(path.join(__dirname, '../public/index.html'));
    });
    
    // Open DevTools in development
    win.webContents.openDevTools();
  } else {
    win.loadFile(path.join(__dirname, '../build/index.html'));
  }

  // Handle navigation errors
  win.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error('Failed to load:', errorCode, errorDescription, validatedURL);
  });
}

app.whenReady().then(() => {
  // Log important paths for debugging
  console.log('=== App Path Information ===');
  console.log('App path:', app.getAppPath());
  console.log('Executable path:', process.execPath);
  console.log('Resources path:', process.resourcesPath);
  console.log('Current working directory:', process.cwd());
  console.log('User data path:', app.getPath('userData'));
  console.log('Executable directory:', path.dirname(process.execPath));
  console.log('========================');
  
  // Check for resources directory existence
  const resourceDirs = [
    process.resourcesPath,
    path.join(process.execPath, '..', 'resources'),
    path.join(path.dirname(process.execPath), 'resources'),
    path.join(app.getAppPath(), '..', 'resources'),
    path.join(app.getPath('exe'), '..', 'resources')
  ];
  
  console.log('=== Resource Directory Check ===');
  resourceDirs.forEach(dir => {
    const exists = fs.existsSync(dir);
    console.log(`${dir}: ${exists ? 'EXISTS' : 'NOT FOUND'}`);
    if (exists) {
      try {
        const files = fs.readdirSync(dir);
        console.log(`Contents of ${dir}:`);
        files.forEach(file => console.log(`- ${file}`));
      } catch (err) {
        console.error(`Error reading directory ${dir}:`, err);
      }
    }
  });
  console.log('================================');
  
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Function to parse client connection events from server logs
function parseClientEvents(logLine, sender) {
  try {
    // Parse client connection: "New WebSocket connection from 127.0.0.1"
    const connectionMatch = logLine.match(/New WebSocket connection from (\d+\.\d+\.\d+\.\d+)/);
    if (connectionMatch) {
      const clientAddress = connectionMatch[1];
      const clientId = `client-${clientAddress}-${Date.now()}`;
      const clientInfo = {
        id: clientId,
        address: clientAddress,
        name: `Client-${clientAddress}`,
        connectedAt: new Date().toLocaleTimeString()
      };
      
      connectedClients.set(clientId, clientInfo);
      console.log('Client connected:', clientInfo);
      sender.send('client-connected', clientInfo);
      return;
    }
    
    // Parse client disconnection: "Client 127.0.0.1 disconnected. Total clients: 0"
    const disconnectionMatch = logLine.match(/Client (\d+\.\d+\.\d+\.\d+) disconnected/);
    if (disconnectionMatch) {
      const clientAddress = disconnectionMatch[1];
      
      // Find and remove the client by address
      for (const [clientId, clientInfo] of connectedClients.entries()) {
        if (clientInfo.address === clientAddress) {
          connectedClients.delete(clientId);
          console.log('Client disconnected:', clientId);
          sender.send('client-disconnected', clientId);
          break;
        }
      }
      return;
    }
  } catch (error) {
    console.error('Error parsing client events:', error);
  }
}

ipcMain.handle('get-clipboard', () => {
  return clipboard.readText();
});

ipcMain.handle('set-clipboard', (event, text) => {
  clipboard.writeText(text);
});

// Server/Client management IPC handlers
ipcMain.handle('start-server', async (event, config) => {
  try {
    if (serverProcess) {
      throw new Error('Server is already running');
    }
    
    // Use helper functions to get the correct Python executable and script paths
    const pythonPath = getPythonExecutablePath();
    const serverScriptPath = getPythonScriptPath();
    
    console.log('Starting server with:');
    console.log('  Python path:', pythonPath);
    console.log('  Script path:', serverScriptPath);
    console.log('  Is development:', isDev);
    console.log('  Resources path:', process.resourcesPath);
    
    // Check if the executable actually exists
    if (!pythonPath && serverScriptPath) {
      console.log('  Server executable exists:', fs.existsSync(serverScriptPath));
      
      // List files in resources directory
      if (fs.existsSync(process.resourcesPath)) {
        console.log('Contents of resources directory:');
        const files = fs.readdirSync(process.resourcesPath);
        files.forEach(file => {
          console.log(`  - ${file}`);
          
          // Check python-standalone directory if it exists
          if (file === 'python-standalone') {
            const standalonePath = path.join(process.resourcesPath, file);
            if (fs.existsSync(standalonePath)) {
              console.log('  Contents of python-standalone directory:');
              const standaloneFiles = fs.readdirSync(standalonePath);
              standaloneFiles.forEach(standaloneFile => {
                console.log(`    - ${standaloneFile}`);
              });
            }
          }
        });
      }
    }
    
    // Build command arguments
    const args = serverScriptPath ? [serverScriptPath] : [];
    
    // Set up environment
    const env = { 
      ...process.env, 
      PORT: config.port.toString(),
      LOG_LEVEL: config.logLevel || 'INFO',
      PYTHONUNBUFFERED: '1',  // Force unbuffered output
      // Force UTF-8 encoding for all Python processes
      PYTHONIOENCODING: 'utf-8',
      LANG: 'en_US.UTF-8',
      LC_ALL: 'en_US.UTF-8',
      LC_CTYPE: 'UTF-8',
    };
    
    // Only add PYTHONPATH in development
    if (isDev) {
      env['PYTHONPATH'] = 'utils/.venv/lib/python3.9/site-packages';
    }
    
    const spawnOptions = {
      env: env,
      cwd: isDev ? path.join(__dirname, '../') : path.dirname(serverScriptPath),
      // @ts-ignore - stdio type issue in VS Code
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: process.platform === 'win32' // Always use shell on Windows for better compatibility
    };
    
    console.log('Spawn options:', spawnOptions);
    console.log('Current working directory:', process.cwd());
    console.log('Resources path:', process.resourcesPath);
    
    // Different handling based on whether we're using standalone executable or Python
    if (pythonPath) {
      // Using Python interpreter
      console.log('Using Python interpreter with args:', args);
      console.log('Python executable exists:', fs.existsSync(pythonPath));
      // @ts-ignore - spawn options type issue
      serverProcess = spawn(pythonPath, args, spawnOptions);
    } else {
      // Using standalone executable directly
      console.log('Using standalone executable directly:', serverScriptPath);
      console.log('Standalone executable exists:', fs.existsSync(serverScriptPath));
      // @ts-ignore - spawn options type issue
      serverProcess = spawn(serverScriptPath, [], spawnOptions);
    }
    
    // Check for ENOENT errors (file not found)
    serverProcess.on('error', error => {
      if ('code' in error && error.code === 'ENOENT') {
        console.error('ENOENT Error: Executable not found!');
        console.error('- Python path:', pythonPath);
        console.error('- Script path:', serverScriptPath);
        console.error('- CWD:', spawnOptions.cwd);
        console.error('- Error:', error.message);
      }
    });

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (serverProcess) {
          serverProcess.kill();
          serverProcess = null;
        }
        reject(new Error('Server startup timeout'));
      }, 60000); // Increased timeout to 60 seconds for packaged apps

      let hasResolved = false;
      let allOutput = '';
      let logBuffer = '';

      serverProcess.stdout.on('data', (data) => {
        logBuffer += data.toString();
        
        // Split by lines and process each complete line
        const lines = logBuffer.split('\n');
        logBuffer = lines.pop(); // Keep the last incomplete line in buffer
        
        lines.forEach(line => {
          if (line.trim()) {
            console.log('Server stdout:', line); // Debug logging
            event.sender.send('server-log', line + '\n');
            
            // Parse client connection events
            parseClientEvents(line, event.sender);
            
            if (line.includes('Server started successfully') && !hasResolved) {
              hasResolved = true;
              clearTimeout(timeout);
              event.sender.send('server-status', 'running');
              resolve({ success: true, message: 'Server started successfully' });
            }
          }
        });
      });

      let errorBuffer = '';

      serverProcess.stderr.on('data', (data) => {
        errorBuffer += data.toString();
        
        // Split by lines and process each complete line
        const lines = errorBuffer.split('\n');
        errorBuffer = lines.pop(); // Keep the last incomplete line in buffer
        
        lines.forEach(line => {
          if (line.trim()) {
            allOutput += 'STDERR: ' + line + '\n';
            console.log('Server stderr:', line); // Debug logging
            
            // Parse client connection events from stderr as well
            parseClientEvents(line, event.sender);
            
            // Check for server startup success in stderr as well
            if (line.includes('Server started successfully') && !hasResolved) {
              hasResolved = true;
              clearTimeout(timeout);
              event.sender.send('server-status', 'running');
              resolve({ success: true, message: 'Server started successfully' });
            }
            
            // Only mark as ERROR if it's actually an error, not debug traces
            if (line.includes('ERROR:') || 
                line.includes('CRITICAL:') ||
                line.includes('ImportError') || 
                line.includes('ModuleNotFoundError') ||
                line.includes('Traceback') ||
                line.includes('Exception')) {
              event.sender.send('server-log', `ERROR: ${line}\n`);
            } else {
              // Send debug/trace output without ERROR prefix
              event.sender.send('server-log', line + '\n');
            }
            
            if (!hasResolved && (line.includes('ImportError') || line.includes('ModuleNotFoundError'))) {
              hasResolved = true;
              clearTimeout(timeout);
              serverProcess = null;
              reject(new Error(`Python dependency error: ${line}`));
            }
          }
        });
      });

      serverProcess.on('exit', (code) => {
        console.log('Server process exited with code:', code); // Debug logging
        console.log('All output was:', allOutput); // Debug logging
        serverProcess = null;
        connectedClients.clear(); // Clear all connected clients when server stops
        event.sender.send('server-status', 'stopped');
        if (code !== 0 && !hasResolved) {
          hasResolved = true;
          clearTimeout(timeout);
          reject(new Error(`Server exited with code ${code}. Output: ${allOutput}`));
        }
      });

      serverProcess.on('error', (error) => {
        console.log('Server process error:', error); // Debug logging
        if (!hasResolved) {
          hasResolved = true;
          clearTimeout(timeout);
          serverProcess = null;
          reject(new Error(`Failed to start server: ${error.message}`));
        }
      });

      // Also check if the process starts at all
      setTimeout(() => {
        if (serverProcess && !hasResolved) {
          console.log('Server process PID:', serverProcess.pid); // Debug logging
          
          // Try to connect to the server to verify it's actually running
          const http = require('http');
          const req = http.get(`http://localhost:${config.port}`, () => {
            if (!hasResolved) {
              hasResolved = true;
              clearTimeout(timeout);
              event.sender.send('server-status', 'running');
              resolve({ success: true, message: 'Server started successfully (verified by connection)' });
            }
          });
          
          req.on('error', (err) => {
            // Server not yet ready, that's okay, we'll keep waiting for the text output
            console.log('Server not yet ready for connections:', err.message);
          });
          
          req.setTimeout(2000);
        }
      }, 3000);  // Check after 3 seconds
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-server', async () => {
  try {
    if (!serverProcess) {
      throw new Error('Server is not running');
    }
    
    connectedClients.clear(); // Clear all connected clients when stopping server
    serverProcess.kill('SIGTERM');
    
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        serverProcess.kill('SIGKILL');
        serverProcess = null;
        resolve({ success: true, message: 'Server stopped (forced)' });
      }, 5000);

      serverProcess.on('exit', () => {
        clearTimeout(timeout);
        serverProcess = null;
        resolve({ success: true, message: 'Server stopped gracefully' });
      });
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('start-client', async (event, config) => {
  try {
    if (clientProcess) {
      throw new Error('Client is already running');
    }
    
    // Use helper functions to get the correct Python executable and script paths
    const pythonPath = getPythonExecutablePath();
    const clientScriptPath = getClientScriptPath();
    
    console.log('Starting client with:');
    console.log('  Python path:', pythonPath);
    console.log('  Script path:', clientScriptPath);
    console.log('  Is development:', isDev);
    console.log('  Resources path:', process.resourcesPath);
    
    // Check if the executable exists
    if (!pythonPath && clientScriptPath) {
      console.log('  Client executable exists:', fs.existsSync(clientScriptPath));
      
      // List files in resources directory
      if (fs.existsSync(process.resourcesPath)) {
        console.log('Contents of resources directory:');
        const files = fs.readdirSync(process.resourcesPath);
        files.forEach(file => {
          console.log(`  - ${file}`);
          
          // Check python-standalone directory if it exists
          if (file === 'python-standalone') {
            const standalonePath = path.join(process.resourcesPath, file);
            if (fs.existsSync(standalonePath)) {
              console.log('  Contents of python-standalone directory:');
              const standaloneFiles = fs.readdirSync(standalonePath);
              standaloneFiles.forEach(standaloneFile => {
                console.log(`    - ${standaloneFile}`);
              });
            }
          }
        });
      }
    }
    
    // Environment setup
    const env = { 
      ...process.env,
      SERVER_HOST: config.serverAddress,
      SERVER_PORT: config.port.toString(),
      LOG_LEVEL: config.logLevel || 'INFO',
      PYTHONUNBUFFERED: '1',
      // Force UTF-8 encoding for all Python processes
      PYTHONIOENCODING: 'utf-8',
      LANG: 'en_US.UTF-8',
      LC_ALL: 'en_US.UTF-8',
      LC_CTYPE: 'UTF-8',
    };
    
    // Only add PYTHONPATH in development
    if (isDev) {
      env['PYTHONPATH'] = 'utils/.venv/lib/python3.9/site-packages';
    }
    
    const spawnOptions = {
      env: env,
      cwd: isDev ? path.join(__dirname, '../') : path.dirname(clientScriptPath),
      shell: process.platform === 'win32' // Always use shell on Windows for better compatibility
    };
    
    // Check if we're using a standalone executable
    if (!pythonPath && !isDev) {
      // Using standalone executable - don't need Python args
      console.log('Using standalone client executable:', clientScriptPath);
      console.log('Standalone executable exists:', fs.existsSync(clientScriptPath));
      console.log('Current working directory:', process.cwd());
      console.log('Resources path:', process.resourcesPath);
      
      // List files in the python-standalone directory to help with debugging
      try {
        const dir = path.dirname(clientScriptPath);
        if (fs.existsSync(dir)) {
          console.log('Contents of python-standalone directory:');
          const files = fs.readdirSync(dir);
          files.forEach(file => {
            console.log('  -', file);
          });
        } else {
          console.error('python-standalone directory does not exist:', dir);
        }
      } catch (err) {
        console.error('Error listing directory:', err);
      }
      
      // Check for file existence and permissions
      if (!fs.existsSync(clientScriptPath)) {
        console.error('Client executable not found at:', clientScriptPath);
        throw new Error(`Client executable not found at: ${clientScriptPath}`);
      }
      
      try {
        console.log('Spawning client process with:');
        console.log('- Executable path:', clientScriptPath);
        console.log('- Arguments:', []);
        console.log('- CWD:', spawnOptions.cwd);
        
        // For Windows, enhanced handling with different approaches
        if (process.platform === 'win32') {
          console.log('Using enhanced Windows compatibility mode');
          
          // Prioritize .bat files over .exe files on Windows
          if (clientScriptPath.endsWith('.bat')) {
            console.log('Using shell:true for Windows .bat file');
            spawnOptions.shell = true;
            spawnOptions.windowsHide = false;
          } else if (clientScriptPath.endsWith('.exe')) {
            console.log('Using Windows .exe specific options');
            spawnOptions.windowsHide = false;
            spawnOptions.windowsVerbatimArguments = true;
          }
          
          // For Windows, add detached option to ensure the process runs independently
          spawnOptions.detached = false;
        }
        
        // Attempt to spawn the process
        console.log('Final spawn options:', JSON.stringify(spawnOptions, null, 2));
        // @ts-ignore - spawn options type issue
        clientProcess = spawn(clientScriptPath, [], spawnOptions);
        
        // Add error handler for file not found or compatibility issues
        clientProcess.on('error', error => {
          console.error('Client process spawn error:', error);
          if ('code' in error && error.code === 'ENOENT') {
            console.error('ENOENT Error: Client executable not found!');
            console.error('- Script path:', clientScriptPath);
            console.error('- CWD:', spawnOptions.cwd);
            console.error('- Error:', error.message);
            
            // Try fallback approach for Windows
            if (process.platform === 'win32') {
              console.log('Attempting Windows fallback method...');
              try {
                const fallbackPath = clientScriptPath.replace('.exe', '.bat');
                if (fs.existsSync(fallbackPath)) {
                  console.log('Found fallback .bat file, trying to use that instead');
                  const fallbackOptions = {
                    ...spawnOptions,
                    shell: true,
                    windowsHide: false
                  };
                  clientProcess = spawn(fallbackPath, [], fallbackOptions);
                }
              } catch (fallbackError) {
                console.error('Fallback attempt failed:', fallbackError);
              }
            }
          } else if ('code' in error && (error.code === 'UNKNOWN' || error.code === 'EACCES')) {
            console.error(`${error.code} Error: This often happens with permission issues or incorrect path.`);
            console.error('- Script path:', clientScriptPath);
            console.error('- File exists:', fs.existsSync(clientScriptPath));
            
            // Try to get file permissions
            try {
              const stats = fs.statSync(clientScriptPath);
              console.error('- File permissions:', stats.mode.toString(8));
              console.error('- Is executable:', (stats.mode & 0o111) !== 0);
            } catch (err) {
              console.error('- Cannot check permissions:', err.message);
            }
          }
        });
      } catch (error) {
        console.error('Error spawning client executable:', error);
        throw error;
      }
    } else {
      // Using Python interpreter
      console.log('Using Python interpreter');
      console.log('Python executable exists:', fs.existsSync(pythonPath));
      // @ts-ignore - spawn options type issue
      clientProcess = spawn(pythonPath, [clientScriptPath], spawnOptions);
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        console.error('Client startup timeout - could not establish connection');
        if (clientProcess) {
          console.log('Client process exists but no success message received');
          console.log('Client process details:');
          console.log('- PID:', clientProcess.pid);
          console.log('- Killed:', clientProcess.killed);
          console.log('- ExitCode:', clientProcess.exitCode);
          
          // Try to force a success resolution instead of failing
          if (clientProcess.pid && clientProcess.exitCode === null) {
            console.log('Process seems to be running, assuming success despite timeout');
            resolve({ success: true, message: 'Client started (assumed running after timeout)' });
            return;
          }
          
          // Kill the process if it's still running
          clientProcess.kill('SIGTERM');
        }
        clientProcess = null;
        reject(new Error('Client startup timeout'));
      }, 10000);

      let clientLogBuffer = '';
      let clientErrorBuffer = '';

      clientProcess.stdout.on('data', (data) => {
        clientLogBuffer += data.toString();
        
        // Split by lines and process each complete line
        const lines = clientLogBuffer.split('\n');
        clientLogBuffer = lines.pop(); // Keep the last incomplete line in buffer
        
        lines.forEach(line => {
          if (line.trim()) {
            event.sender.send('client-log', line + '\n');
            if (line.includes('Connected to server successfully')) {
              clearTimeout(timeout);
              resolve({ success: true, message: 'Client connected successfully' });
            }
          }
        });
      });

      clientProcess.stderr.on('data', (data) => {
        clientErrorBuffer += data.toString();
        
        // Split by lines and process each complete line
        const lines = clientErrorBuffer.split('\n');
        clientErrorBuffer = lines.pop(); // Keep the last incomplete line in buffer
        
        lines.forEach(line => {
          if (line.trim()) {
            // Check for success message from ui_logger
            if (line.includes('Connected to server successfully')) {
              clearTimeout(timeout);
              resolve({ success: true, message: 'Client connected successfully' });
            }
            
            // Only mark as ERROR if it's actually an error, not debug traces
            if (line.includes('ERROR:') || 
                line.includes('CRITICAL:') ||
                line.includes('ImportError') || 
                line.includes('ModuleNotFoundError') ||
                line.includes('Traceback') ||
                line.includes('Exception')) {
              event.sender.send('client-log', `ERROR: ${line}\n`);
            } else {
              // Send debug/trace output without ERROR prefix
              event.sender.send('client-log', line + '\n');
            }
          }
        });
      });

      clientProcess.on('exit', (code) => {
        clientProcess = null;
        event.sender.send('client-status', 'stopped');
        if (code !== 0) {
          clearTimeout(timeout);
          reject(new Error(`Client exited with code ${code}`));
        }
      });
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('stop-client', async () => {
  try {
    if (!clientProcess) {
      throw new Error('Client is not running');
    }
    
    clientProcess.kill('SIGTERM');
    
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        clientProcess.kill('SIGKILL');
        clientProcess = null;
        resolve({ success: true, message: 'Client stopped (forced)' });
      }, 5000);

      clientProcess.on('exit', () => {
        clearTimeout(timeout);
        clientProcess = null;
        resolve({ success: true, message: 'Client stopped gracefully' });
      });
    });
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-service-status', () => {
  return {
    server: serverProcess ? 'running' : 'stopped',
    client: clientProcess ? 'running' : 'stopped'
  };
});

ipcMain.handle('get-connected-clients', () => {
  // Return array of connected client info
  return Array.from(connectedClients.values());
});

// Cleanup on app quit
app.on('before-quit', () => {
  if (serverProcess) {
    serverProcess.kill('SIGTERM');
  }
  if (clientProcess) {
    clientProcess.kill('SIGTERM');
  }
});
