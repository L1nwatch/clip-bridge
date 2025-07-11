const { app, BrowserWindow, ipcMain, clipboard } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

const isDev = process.env.NODE_ENV === 'development';

let serverProcess = null;
let clientProcess = null;

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
      enableRemoteModule: false,
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
    win.loadURL('http://localhost:3000').catch(err => {
      console.error('Failed to load development URL:', err);
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
  createWindow();

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

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
    
    // Use system python3 with virtual environment path
    const pythonPath = 'python3';
    
    const serverPath = path.join(__dirname, '../utils/server.py');
    
    serverProcess = spawn(pythonPath, [serverPath], {
      env: { 
        ...process.env, 
        PORT: config.port.toString(),
        LOG_LEVEL: config.logLevel || 'INFO',
        PYTHONUNBUFFERED: '1',  // Force unbuffered output
        PYTHONPATH: 'utils/.venv/lib/python3.9/site-packages'
      },
      cwd: path.join(__dirname, '../'),  // Changed to parent directory so utils/ path works
      stdio: ['pipe', 'pipe', 'pipe']  // Explicit stdio configuration
    });

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (serverProcess) {
          serverProcess.kill();
          serverProcess = null;
        }
        reject(new Error('Server startup timeout'));
      }, 15000); // Increased timeout

      let hasResolved = false;
      let allOutput = '';

      serverProcess.stdout.on('data', (data) => {
        const message = data.toString();
        allOutput += message;
        console.log('Server stdout:', message); // Debug logging
        event.sender.send('server-log', message);
        if (message.includes('Server started successfully') && !hasResolved) {
          hasResolved = true;
          clearTimeout(timeout);
          event.sender.send('server-status', 'running');
          resolve({ success: true, message: 'Server started successfully' });
        }
      });

      serverProcess.stderr.on('data', (data) => {
        const errorMessage = data.toString();
        allOutput += 'STDERR: ' + errorMessage;
        console.log('Server stderr:', errorMessage); // Debug logging
        event.sender.send('server-log', `ERROR: ${errorMessage}`);
        if (!hasResolved && (errorMessage.includes('ImportError') || errorMessage.includes('ModuleNotFoundError'))) {
          hasResolved = true;
          clearTimeout(timeout);
          serverProcess = null;
          reject(new Error(`Python dependency error: ${errorMessage}`));
        }
      });

      serverProcess.on('exit', (code) => {
        console.log('Server process exited with code:', code); // Debug logging
        console.log('All output was:', allOutput); // Debug logging
        serverProcess = null;
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
    
    const pythonPath = path.join(__dirname, '../utils/.venv/bin/python');
    const clientPath = path.join(__dirname, '../utils/client.py');
    
    clientProcess = spawn(pythonPath, [clientPath], {
      env: { 
        ...process.env,
        SERVER_HOST: config.serverAddress,
        SERVER_PORT: config.port.toString(),
        LOG_LEVEL: config.logLevel || 'INFO'
      }
    });

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error('Client startup timeout'));
      }, 10000);

      clientProcess.stdout.on('data', (data) => {
        const message = data.toString();
        event.sender.send('client-log', message);
        if (message.includes('WebSocket connection established')) {
          clearTimeout(timeout);
          resolve({ success: true, message: 'Client connected successfully' });
        }
      });

      clientProcess.stderr.on('data', (data) => {
        event.sender.send('client-log', `ERROR: ${data.toString()}`);
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

// Cleanup on app quit
app.on('before-quit', () => {
  if (serverProcess) {
    serverProcess.kill('SIGTERM');
  }
  if (clientProcess) {
    clientProcess.kill('SIGTERM');
  }
});
