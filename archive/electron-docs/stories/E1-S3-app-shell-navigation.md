# Story E1-S3: Create Main Application Shell with Navigation

## Status
Draft

## Story
**As a** clinical user,
**I want** a main application window with sidebar navigation,
**so that** I can easily access different features of Patient Explorer.

## Acceptance Criteria
1. Sidebar navigation displays with icons and labels
2. Navigation items include: Capture, Patients, Follow-Ups, Reports, Settings
3. Active navigation item is visually highlighted
4. Sidebar can collapse to icon-only mode (240px → 64px)
5. Header displays app title and sync status badge placeholder
6. Content area renders placeholder for each route
7. Home Team branding colors are applied (#12A865 primary green)

## Tasks / Subtasks
- [ ] Set up React Router (AC: 6)
  - [ ] npm install react-router-dom
  - [ ] Create src/renderer/routes.tsx
  - [ ] Define routes for each navigation item
- [ ] Create layout components (AC: 1, 5)
  - [ ] Create src/renderer/components/layout/AppShell.tsx
  - [ ] Create src/renderer/components/layout/Sidebar.tsx
  - [ ] Create src/renderer/components/layout/Header.tsx
  - [ ] Create src/renderer/components/layout/MainContent.tsx
- [ ] Implement sidebar navigation (AC: 1, 2, 3, 4)
  - [ ] Create NavigationItem component
  - [ ] Add icons using lucide-react
  - [ ] Implement active state styling
  - [ ] Add collapse/expand functionality with localStorage persistence
- [ ] Set up Tailwind CSS (AC: 7)
  - [ ] npm install tailwindcss postcss autoprefixer
  - [ ] Create tailwind.config.js with custom colors
  - [ ] Configure primary green: #12A865
  - [ ] Set up design tokens from frontend-spec
- [ ] Create placeholder pages (AC: 6)
  - [ ] CaptureScreen.tsx
  - [ ] PatientsScreen.tsx
  - [ ] FollowUpsScreen.tsx
  - [ ] ReportsScreen.tsx
  - [ ] SettingsScreen.tsx
- [ ] Add sync status badge (AC: 5)
  - [ ] Create SyncStatusBadge component (placeholder)
  - [ ] Position in header right side

## Dev Notes

### Application Shell Layout (from Frontend Spec §4.1)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ▪ ▪ ▪  Patient Explorer                       [Sync: ✓ 2s ago]  [─][□][×] │
├──────────────────┬──────────────────────────────────────────────────────────┤
│                  │                                                          │
│  🏥 Green Clinic │                                                          │
│                  │                     MAIN CONTENT AREA                    │
│  ──────────────  │                                                          │
│  📋 Capture    ● │                     (varies by screen)                   │
│  📁 Patients     │                                                          │
│  📅 Follow-Ups   │                                                          │
│  📊 Reports      │                                                          │
│                  │                                                          │
│  ──────────────  │                                                          │
│  ⚙️ Settings     │                                                          │
│  👤 User       ▼ │                                                          │
└──────────────────┴──────────────────────────────────────────────────────────┘
```

### Design Tokens (from Frontend Spec §3)
```typescript
// tailwind.config.js
export default {
  theme: {
    extend: {
      colors: {
        primary: {
          900: '#0D5C3D',
          700: '#0F7A4F',
          500: '#12A865',  // Main brand
          300: '#5DC98E',
          100: '#B8E8CF',
        },
        neutral: {
          950: '#0F172A',
          700: '#334155',
          500: '#64748B',
          400: '#94A3B8',
          200: '#E2E8F0',
          50: '#F8FAFC',
        },
      },
    },
  },
};
```

### Navigation Items
| Route | Label | Icon (lucide-react) |
|-------|-------|---------------------|
| /capture | Capture | Camera |
| /patients | Patients | FolderOpen |
| /follow-ups | Follow-Ups | Calendar |
| /reports | Reports | BarChart3 |
| /settings | Settings | Settings |

### Sidebar Specifications
- Expanded width: 240px
- Collapsed width: 64px
- Background: neutral-50
- Active item: primary-100 background, primary-500 left border (4px)

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Navigation renders all items
  - Click navigates to correct route
  - Collapse/expand works
  - Active state applies correctly

## Change Log
| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-11-30 | 1.0 | Initial story draft | Bob (SM) |

---

## Dev Agent Record
### Agent Model Used
### Debug Log References
### Completion Notes
### File List

---

## QA Results
