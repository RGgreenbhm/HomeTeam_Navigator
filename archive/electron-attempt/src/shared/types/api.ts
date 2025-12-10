/**
 * Patient Explorer - API Types
 *
 * Type definitions for IPC communication between main and renderer
 */

// App API
export interface AppAPI {
  getVersion: () => Promise<string>;
  getPlatform: () => Promise<NodeJS.Platform>;
}

// Future: Patient types (E3)
// export interface Patient {
//   id: string;
//   mrn: string;
//   firstName: string;
//   lastName: string;
//   dateOfBirth: string;
//   // ... more fields
// }

// Future: Capture types (E2)
// export interface Capture {
//   id: string;
//   patientId: string;
//   imageBlob: Blob;
//   extractedText: string;
//   captureType: CaptureType;
//   // ... more fields
// }

// Future: Auth types (E5)
// export interface Session {
//   userId: string;
//   username: string;
//   role: 'admin' | 'user';
//   token: string;
// }

// Main API exposed to renderer via preload
export interface ElectronAPI extends AppAPI {
  // Future: Add patient, capture, auth APIs
}

// Type augmentation for window.api
declare global {
  interface Window {
    api: ElectronAPI;
  }
}
