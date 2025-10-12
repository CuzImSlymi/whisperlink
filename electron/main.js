const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = process.env.ELECTRON_IS_DEV === 'true';
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  // Create the browser window with dark theme
  const windowOptions = {
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#0d1117',
    show: false,
    vibrancy: 'dark', // macOS vibrancy effect
    transparent: false,
    titleBarOverlay: false
  };

  // Platform-specific styling
  if (process.platform === 'darwin') {
    // macOS specific settings
    windowOptions.titleBarStyle = 'hiddenInset';
    windowOptions.trafficLightPosition = { x: 20, y: 20 };
    windowOptions.fullscreenable = true;
    windowOptions.maximizable = true;
  } else {
    // Windows/Linux
    windowOptions.frame = false;
    windowOptions.titleBarStyle = 'hidden';
  }

  try {
    if (process.platform !== 'darwin') {
      const iconPath = path.join(__dirname, '../assets/icon.png');
      if (require('fs').existsSync(iconPath)) {
        windowOptions.icon = iconPath;
      }
    }
  } catch (error) {
    console.log('Icon file not found, proceeding without icon');
  }

  mainWindow = new BrowserWindow(windowOptions);

  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Show window when ready to prevent visual flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Open DevTools in development
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Start Python backend process
function startPythonBackend() {
  // Don't start if already running
  if (pythonProcess && !pythonProcess.killed && pythonProcess.exitCode === null) {
    console.log('Python process already running');
    return;
  }

  const pythonScript = path.join(__dirname, '../python_bridge.py');
  
  // Try python3 first, fallback to python
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  
  console.log('Starting Python bridge...');
  
  try {
    pythonProcess = spawn(pythonCmd, [pythonScript], {
      stdio: ['pipe', 'pipe', 'pipe'],
      cwd: path.join(__dirname, '..')
    });

    pythonProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      if (output) {
        console.log(`Python: ${output}`);
      }
    });

    pythonProcess.stderr.on('data', (data) => {
      const errorOutput = data.toString().trim();
      if (errorOutput) {
        console.error(`Python Error: ${errorOutput}`);
      }
    });

    pythonProcess.on('close', (code) => {
      console.log(`Python process exited with code ${code}`);
      pythonProcess = null;
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      pythonProcess = null;
    });

    // Give the Python process time to initialize
    setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed && pythonProcess.exitCode === null) {
        console.log('Python bridge initialized successfully');
      } else {
        console.error('Python bridge failed to initialize');
      }
    }, 2000);
    
  } catch (error) {
    console.error('Error spawning Python process:', error);
    pythonProcess = null;
  }
}

// Stop Python backend process
function stopPythonBackend() {
  if (pythonProcess && !pythonProcess.killed) {
    console.log('Stopping Python bridge...');
    pythonProcess.kill('SIGTERM');
    
    // Force kill after 5 seconds if still running
    setTimeout(() => {
      if (pythonProcess && !pythonProcess.killed) {
        console.log('Force killing Python process...');
        pythonProcess.kill('SIGKILL');
      }
    }, 5000);
  }
  pythonProcess = null;
}

// App event handlers
app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
      // Restart Python bridge if needed when reactivating on macOS
      if (!pythonProcess || pythonProcess.killed || pythonProcess.exitCode !== null) {
        startPythonBackend();
      }
    }
  });
});

app.on('window-all-closed', () => {
  stopPythonBackend();
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopPythonBackend();
});

// IPC handlers for communication with renderer
ipcMain.handle('restart-python-bridge', async () => {
  console.log('Restarting Python bridge...');
  stopPythonBackend();
  
  // Wait a moment before restarting
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  startPythonBackend();
  
  // Wait for initialization
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  return { success: true, message: 'Python bridge restarted' };
});

ipcMain.handle('python-command', async (event, command, args) => {
  return new Promise((resolve, reject) => {
    if (!pythonProcess) {
      reject(new Error('Python process not available'));
      return;
    }

    // Check if process is still alive
    if (pythonProcess.killed || pythonProcess.exitCode !== null) {
      reject(new Error('Python process is not running'));
      return;
    }

    // Send command to Python process
    const message = JSON.stringify({ command, args }) + '\n';
    
    let buffer = '';
    let timeoutId;
    let isResolved = false;
    
    // Set up response handler
    const responseHandler = (data) => {
      if (isResolved) return;
      
      try {
        buffer += data.toString();
        const lines = buffer.split('\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              const response = JSON.parse(line);
              cleanup();
              isResolved = true;
              resolve(response);
              return;
            } catch (parseError) {
              console.error('JSON parse error for line:', line, parseError);
            }
          }
        }
        
        // Keep the last incomplete line in buffer
        buffer = lines[lines.length - 1];
        
      } catch (error) {
        console.error('Python response parse error:', error);
        cleanup();
        if (!isResolved) {
          isResolved = true;
          reject(error);
        }
      }
    };

    const errorHandler = (error) => {
      if (isResolved) return;
      console.error('Python process error:', error);
      cleanup();
      isResolved = true;
      reject(new Error('Python process error: ' + error.message));
    };

    const cleanup = () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
      pythonProcess.stdout.removeListener('data', responseHandler);
      pythonProcess.removeListener('error', errorHandler);
    };
    
    // Set up listeners
    pythonProcess.stdout.on('data', responseHandler);
    pythonProcess.on('error', errorHandler);
    
    // Send the command
    try {
      pythonProcess.stdin.write(message);
    } catch (writeError) {
      cleanup();
      isResolved = true;
      reject(new Error('Failed to send command to Python process: ' + writeError.message));
      return;
    }
    
    // Timeout after 15 seconds (increased from 10)
    timeoutId = setTimeout(() => {
      if (!isResolved) {
        cleanup();
        isResolved = true;
        reject(new Error('Python command timeout'));
      }
    }, 15000);
  });
});

// Window control handlers
ipcMain.handle('window-minimize', () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.handle('window-close', () => {
  if (mainWindow) {
    mainWindow.close();
  }
});