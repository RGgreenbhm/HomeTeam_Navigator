# Story E1-S5: Add Home Team Branding (Icons, Colors, Splash)

## Status
Draft

## Story
**As a** clinical user,
**I want** the application styled with Home Team branding,
**so that** it feels familiar and professional to our team.

## Acceptance Criteria
1. HTnav icons display correctly in navigation and UI
2. Primary green color (#12A865) is used throughout
3. Splash screen shows on application startup
4. App icon is set in taskbar and window title
5. About dialog displays version and clinic info
6. Inter font is loaded for UI text

## Tasks / Subtasks
- [ ] Import brand assets (AC: 1)
  - [ ] Copy HTnav icon set to src/renderer/assets/icons/
  - [ ] Copy splash image to src/renderer/assets/
  - [ ] Copy app icon (ico/png) for Electron
- [ ] Configure app icon (AC: 4)
  - [ ] Create icon.ico for Windows
  - [ ] Update electron-builder.yml with icon path
  - [ ] Set window title to "Patient Explorer"
- [ ] Create splash screen (AC: 3)
  - [ ] Create SplashScreen component
  - [ ] Show during initial database load
  - [ ] Display Home Team Logic image
  - [ ] Auto-dismiss after loading (or 2s minimum)
- [ ] Configure typography (AC: 6)
  - [ ] Add Inter font (Google Fonts or local)
  - [ ] Add JetBrains Mono for monospace
  - [ ] Configure Tailwind font families
- [ ] Create About dialog (AC: 5)
  - [ ] Show app version from package.json
  - [ ] Display "Green Clinic" and copyright
  - [ ] Include HIPAA compliance badge
- [ ] Apply brand colors throughout (AC: 2)
  - [ ] Update Tailwind config with full palette
  - [ ] Apply primary-500 to active states
  - [ ] Apply neutral palette to backgrounds

## Dev Notes

### Brand Asset Mapping (from PRD)
| Icon File | Usage |
|-----------|-------|
| HTnav_clipboard.png | Patient Detail, Notes |
| HTnav_folder.png | Patient Files |
| HTnav_magnifying glass.png | Search, Capture |
| HTnav_team.png | User Management |
| HTnav_cellphone.png | Spruce Communications |
| HTnav_payclock.png | Scheduling, Follow-Up |
| Image_Home Team Logic.png | Splash Screen, About |

### Color Palette (from Frontend Spec §3.1)
```css
/* Primary (Green Clinic) */
--primary-900: #0D5C3D;
--primary-700: #0F7A4F;
--primary-500: #12A865;  /* Main brand */
--primary-300: #5DC98E;
--primary-100: #B8E8CF;

/* Neutral */
--neutral-950: #0F172A;  /* Text */
--neutral-50: #F8FAFC;   /* Background */

/* Status */
--success: #22C55E;
--warning: #EAB308;
--error: #EF4444;
```

### Typography (from Frontend Spec §3.2)
```typescript
// tailwind.config.js
fontFamily: {
  sans: ['Inter', 'system-ui', 'sans-serif'],
  mono: ['JetBrains Mono', 'Consolas', 'monospace'],
},
fontSize: {
  xs: ['12px', '16px'],
  sm: ['14px', '20px'],
  base: ['16px', '24px'],
  lg: ['18px', '28px'],
  xl: ['20px', '28px'],
  '2xl': ['24px', '32px'],
},
```

### Splash Screen Duration
- Minimum display: 2 seconds
- Maximum display: Until database ready
- Show loading indicator if > 2s

## Testing
- **Location**: `src/renderer/components/__tests__/`
- **Framework**: Vitest + React Testing Library
- **Required Tests**:
  - Splash screen renders
  - About dialog opens and closes
  - Icons load without errors
- **Visual**: Manual verification of colors and fonts

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
