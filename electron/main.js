const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = process.env.ELECTRON_IS_DEV === 'true';
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  // Create the browser window with dark theme
  mainWindow = new BrowserWindow({
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
    titleBarStyle: 'hiddenInset',
    backgroundColor: '#0d1117',
    show: false,
    icon: path.join(__dirname, '../assets/icon.png')
  });

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
  const pythonScript = path.join(__dirname, '../python_bridge.py');
  pythonProcess = spawn('python3', [pythonScript], {
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd: path.join(__dirname, '..')
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data.toString().trim()}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

// App event handlers
app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// IPC handlers for communication with renderer
ipcMain.handle('python-command', async (event, command, args) => {
  return new Promise((resolve, reject) => {
    if (!pythonProcess) {
      reject(new Error('Python process not available'));
      return;
    }

    // Send command to Python process
    const message = JSON.stringify({ command, args }) + '\n';
    pythonProcess.stdin.write(message);
    
    let buffer = '';
    
    // Set up response handler
    const responseHandler = (data) => {
      try {
        buffer += data.toString();
        const lines = buffer.split('\n');
        
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (line && line.startsWith('{')) {
            try {
              const response = JSON.parse(line);
              pythonProcess.stdout.removeListener('data', responseHandler);
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
        pythonProcess.stdout.removeListener('data', responseHandler);
        reject(error);
      }
    };
    
    pythonProcess.stdout.on('data', responseHandler);
    
    // Timeout after 10 seconds
    setTimeout(() => {
      pythonProcess.stdout.removeListener('data', responseHandler);
      reject(new Error('Python command timeout'));
    }, 10000);
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