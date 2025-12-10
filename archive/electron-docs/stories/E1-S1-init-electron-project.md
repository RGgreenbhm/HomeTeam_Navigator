# Story E1-S1: Initialize Electron + React + TypeScript Project

## Status
In Progress

## Story
**As a** developer,
**I want** an Electron application scaffolded with React and TypeScript,
**so that** I have a solid foundation to build the Patient Explorer desktop app.

## Acceptance Criteria
1. Project initializes with `npm install` without errors
2. Application launches with `npm run dev` showing a blank Electron window
3. React 18 is configured with TypeScript 5.3+
4. Vite is configured as the build tool with HMR working
5. Electron 28.x LTS is installed with proper main/renderer process separation
6. ESLint and Prettier are configured with recommended rules
7. Project structure follows the architecture document conventions

## Tasks / Subtasks
- [ ] Initialize npm project with package.json (AC: 1)
  - [ ] Set name: "patient-explorer"
  - [ ] Set version: "0.1.0"
  - [ ] Configure scripts: dev, build, lint, test
- [ ] Install core dependencies (AC: 2, 3, 4, 5)
  - [ ] electron@28.x
  - [ ] react@18.x, react-dom@18.x
  - [ ] typescript@5.3+
  - [ ] vite@5.x, @vitejs/plugin-react
  - [ ] electron-builder@24.x
- [ ] Configure TypeScript (AC: 3)
  - [ ] Create tsconfig.json with strict mode
  - [ ] Create tsconfig.node.json for main process
  - [ ] Configure path aliases
- [ ] Set up Vite configuration (AC: 4)
  - [ ] Create vite.config.ts for renderer
  - [ ] Configure HMR for development
  - [ ] Set up build output for production
- [ ] Create Electron main process (AC: 5)
  - [ ] Create src/main/index.ts
  - [ ] Configure BrowserWindow with secure defaults
  - [ ] Set up preload script structure
- [ ] Create React renderer process (AC: 3, 5)
  - [ ] Create src/renderer/index.tsx entry point
  - [ ] Create src/renderer/App.tsx with basic component
  - [ ] Create index.html template
- [ ] Configure linting (AC: 6)
  - [ ] Install eslint, @typescript-eslint/\*, prettier
  - [ ] Create .eslintrc.js with recommended rules
  - [ ] Create .prettierrc with project conventions
- [ ] Create project structure (AC: 7)
  - [ ] src/main/ - Electron main process
  - [ ] src/renderer/ - React UI
  - [ ] src/preload/ - Preload scripts
  - [ ] src/shared/ - Shared types

## Dev Notes

### Project Structure (from Architecture §2.2)
```
patient-explorer/
├── src/
│   ├── main/           # Electron main process
│   │   ├── index.ts    # Entry point
│   │   ├── ipc/        # IPC handlers
│   │   └── services/   # Business logic
│   ├── renderer/       # React UI
│   │   ├── index.tsx   # Entry point
│   │   ├── App.tsx     # Root component
│   │   └── components/ # UI components
│   ├── preload/        # Preload scripts
│   │   └── index.ts    # contextBridge API
│   └── shared/         # Shared types
│       └── types/      # TypeScript interfaces
├── package.json
├── tsconfig.json
├── vite.config.ts
└── electron-builder.yml
```

### Electron Security Defaults
```typescript
// BrowserWindow config (from Architecture §5)
const mainWindow = new BrowserWindow({
  width: 1280,
  height: 800,
  webPreferences: {
    nodeIntegration: false,      // SECURITY: Disable Node in renderer
    contextIsolation: true,      // SECURITY: Enable context isolation
    sandbox: true,               // SECURITY: Enable sandbox
    preload: path.join(__dirname, 'preload.js'),
  },
});
```

### Package Versions (from Architecture §3.1)
- Electron: 28.x LTS
- React: 18.x
- TypeScript: 5.3+
- Vite: 5.x
- electron-builder: 24.x

## Testing
- **Location**: `src/__tests__/` or alongside source files
- **Framework**: Vitest (from Architecture §8)
- **This story**: No unit tests required (scaffolding only)
- **Verification**: Run `npm run dev` and confirm window appears

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story draft | Bob (SM) |

---

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References
N/A - Initial scaffolding

### Completion Notes
Project structure created with all required configuration files:
- Electron 28.x with secure BrowserWindow defaults
- React 18 with TypeScript 5.3+ strict mode
- Vite 5.x with HMR and electron plugin
- TailwindCSS with Home Team brand colors
- ESLint + Prettier with recommended rules
- Vitest configured for unit testing

**Next Step**: Run `npm install` to install dependencies, then `npm run dev` to verify

### File List
- `package.json` - Project dependencies and scripts
- `tsconfig.json` - TypeScript config (renderer)
- `tsconfig.node.json` - TypeScript config (main process)
- `vite.config.ts` - Vite bundler configuration
- `.eslintrc.cjs` - ESLint rules
- `.prettierrc` - Prettier formatting rules
- `.gitignore` - Git ignore patterns
- `tailwind.config.js` - Tailwind CSS configuration
- `postcss.config.js` - PostCSS plugins
- `vitest.config.ts` - Vitest test configuration
- `electron-builder.yml` - Production build config
- `index.html` - HTML entry point
- `src/main/index.ts` - Electron main process
- `src/preload/index.ts` - Preload script with contextBridge
- `src/renderer/index.tsx` - React entry point
- `src/renderer/App.tsx` - Root React component
- `src/renderer/styles/index.css` - Global styles with Tailwind
- `src/shared/types/index.ts` - Shared type exports
- `src/shared/types/api.ts` - API type definitions
- `src/test/setup.ts` - Vitest setup file

---

## QA Results
*(To be completed by QA agent)*
