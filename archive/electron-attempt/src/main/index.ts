/**
 * Patient Explorer - Electron Main Process
 *
 * HIPAA-compliant patient data aggregation tool
 * Main process handles: window management, IPC, database, security
 */

import { app, BrowserWindow, ipcMain } from 'electron';
import path from 'path';

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

// Security: Disable remote module (deprecated)
app.on('remote-require', (event) => event.preventDefault());
app.on('remote-get-builtin', (event) => event.preventDefault());
app.on('remote-get-global', (event) => event.preventDefault());
app.on('remote-get-current-window', (event) => event.preventDefault());
app.on('remote-get-current-web-contents', (event) => event.preventDefault());

let mainWindow: BrowserWindow | null = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

function createWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    title: 'Patient Explorer',
    show: false, // Show when ready to prevent flash
    backgroundColor: '#f8fafc', // Tailwind slate-50

    webPreferences: {
      // SECURITY: Critical settings for HIPAA compliance
      nodeIntegration: false, // Never enable in renderer
      contextIsolation: true, // Required for secure IPC
      sandbox: true, // Additional isolation
      webSecurity: true, // Enforce same-origin policy
      allowRunningInsecureContent: false,
      preload: path.join(__dirname, '../preload/index.js'),
    },
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    if (isDev) {
      mainWindow?.webContents.openDevTools();
    }
  });

  // Load the app
  if (isDev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL']);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // macOS: re-create window when dock icon clicked
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed (except on macOS)
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

// Basic IPC handlers (placeholder for future implementation)
ipcMain.handle('app:getVersion', () => {
  return app.getVersion();
});

ipcMain.handle('app:getPlatform', () => {
  return process.platform;
});
