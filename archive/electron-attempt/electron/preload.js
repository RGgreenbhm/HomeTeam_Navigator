/**
 * Patient Explorer - Preload Script
 *
 * Exposes a secure, limited API to the renderer process
 * using contextBridge.
 */

const { contextBridge, ipcRenderer } = require('electron');

// Type-safe API exposed to renderer
const electronAPI = {
  getVersion: () => ipcRenderer.invoke('app:getVersion'),
  getPlatform: () => ipcRenderer.invoke('app:getPlatform'),
};

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('api', electronAPI);
