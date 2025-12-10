/**
 * Patient Explorer - Preload Script
 *
 * Exposes a secure, limited API to the renderer process
 * using contextBridge. This is the ONLY way renderer can
 * communicate with the main process.
 */

import { contextBridge, ipcRenderer } from 'electron';

// Type-safe API exposed to renderer
const electronAPI = {
  // App information
  getVersion: (): Promise<string> => ipcRenderer.invoke('app:getVersion'),
  getPlatform: (): Promise<NodeJS.Platform> => ipcRenderer.invoke('app:getPlatform'),

  // Future: Patient operations (E3)
  // patient: {
  //   list: (params) => ipcRenderer.invoke('patient:list', params),
  //   get: (id) => ipcRenderer.invoke('patient:get', { id }),
  //   create: (data) => ipcRenderer.invoke('patient:create', data),
  //   update: (id, data) => ipcRenderer.invoke('patient:update', { id, ...data }),
  // },

  // Future: Capture operations (E2)
  // capture: {
  //   save: (data) => ipcRenderer.invoke('capture:save', data),
  //   listByPatient: (patientId) => ipcRenderer.invoke('capture:listByPatient', { patientId }),
  // },

  // Future: Auth operations (E5)
  // auth: {
  //   login: (credentials) => ipcRenderer.invoke('auth:login', credentials),
  //   logout: () => ipcRenderer.invoke('auth:logout'),
  //   validate: () => ipcRenderer.invoke('auth:validate'),
  // },
};

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('api', electronAPI);

// Type declaration for renderer
declare global {
  interface Window {
    api: typeof electronAPI;
  }
}
