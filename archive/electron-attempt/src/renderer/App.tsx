/**
 * Patient Explorer - Root Application Component
 *
 * HIPAA-compliant patient data aggregation tool for Green Clinic
 */

import { useEffect, useState } from 'react';

function App() {
  const [appVersion, setAppVersion] = useState<string>('');
  const [platform, setPlatform] = useState<string>('');

  useEffect(() => {
    // Get app info from main process
    async function loadAppInfo() {
      try {
        const version = await window.api.getVersion();
        const platformInfo = await window.api.getPlatform();
        setAppVersion(version);
        setPlatform(platformInfo);
      } catch (error) {
        console.error('Failed to load app info:', error);
      }
    }
    loadAppInfo();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">PE</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900">Patient Explorer</h1>
              <p className="text-sm text-slate-500">Green Clinic</p>
            </div>
          </div>
          <div className="text-sm text-slate-400">
            {appVersion && `v${appVersion}`} • {platform}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="max-w-4xl mx-auto">
          {/* Welcome Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-8 text-center">
            <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg
                className="w-10 h-10 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                />
              </svg>
            </div>

            <h2 className="text-2xl font-bold text-slate-900 mb-2">
              Welcome to Patient Explorer
            </h2>
            <p className="text-slate-600 mb-6 max-w-md mx-auto">
              HIPAA-compliant patient data capture and organization for Green Clinic.
              Securely manage patient records during EMR transitions.
            </p>

            {/* Status Badges */}
            <div className="flex items-center justify-center gap-4 mb-8">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Electron Ready
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                React 18
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                TypeScript
              </span>
            </div>

            {/* Next Steps */}
            <div className="bg-slate-50 rounded-lg p-4 text-left">
              <h3 className="font-medium text-slate-900 mb-2">Implementation Progress</h3>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-center gap-2">
                  <span className="text-green-500">✓</span>
                  E1-S1: Electron + React + TypeScript initialized
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-slate-300">○</span>
                  E1-S2: SQLite + SQLCipher database layer
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-slate-300">○</span>
                  E1-S3: Application shell with navigation
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-slate-300">○</span>
                  E1-S4: Patient data model and schema
                </li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 px-6 py-3">
        <p className="text-center text-sm text-slate-500">
          Home Team Medical Services • HIPAA Compliant • Green Clinic Deployment
        </p>
      </footer>
    </div>
  );
}

export default App;
