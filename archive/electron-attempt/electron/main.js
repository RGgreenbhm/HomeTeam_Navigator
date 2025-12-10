/**
 * Patient Explorer - Electron Main Process
 *
 * HIPAA-compliant patient data aggregation tool
 * Main process handles: window management, IPC, database, security
 */

// Debug: Check what require('electron') returns
const electronModule = require('electron');
console.log('Electron module type:', typeof electronModule);
console.log('Electron module keys:', Object.keys(electronModule || {}));
console.log('Electron module value:', electronModule);

const { app, BrowserWindow, ipcMain } = electronModule;
const path = require('path');

if (!app) {
  console.error('ERROR: app is undefined. require("electron") returned:', electronModule);
  process.exit(1);
}

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

// Security: Disable remote module (deprecated)
app.on('remote-require', (event) => event.preventDefault());
app.on('remote-get-builtin', (event) => event.preventDefault());
app.on('remote-get-global', (event) => event.preventDefault());
app.on('remote-get-current-window', (event) => event.preventDefault());
app.on('remote-get-current-web-contents', (event) => event.preventDefault());

let mainWindow = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    title: 'Patient Explorer',
    show: false,
    backgroundColor: '#f8fafc',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/renderer/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// Security: Prevent new window creation
app.on('web-contents-created', (_, contents) => {
  contents.on('will-navigate', (event) => {
    event.preventDefault();
  });

  contents.setWindowOpenHandler(() => {
    return { action: 'deny' };
  });
});

// Basic IPC handlers
ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

ipcMain.handle('app:getPlatform', () => {
  return process.platform;
});
