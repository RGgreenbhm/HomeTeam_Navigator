# Patient Explorer - Project Context

## Project Overview
**Purpose:** A HIPAA-compliant patient data aggregation tool for capturing, organizing, and searching patient information from multiple EMR sources (Allscripts, Athena One) during practice transition and consolidation.

**Status:** Greenfield / Phase 1 - Capture & Storage

**Owner:** Home Team Medical Services

---

## Team Structure
| Role | Person | Focus Area |
|------|--------|------------|
| President / CMO / Requirements | RG | Domain expertise, workflow design, UI concepts |
| CEO | Pat Rutledge | VS Code, Claude Code, implementation |
| CTO | Pavel Savine | Backend development, architecture, security |

---

## BMAD Analyst Persona Context

When working on requirements, user stories, or feature definitions, adopt the **Analyst** mindset:

### Primary Objectives
- Elicit clear, testable requirements from the domain expert (RG)
- Translate clinical workflows into user stories with acceptance criteria
- Ensure HIPAA compliance is baked into every requirement
- Keep scope focused on Phase 1: Capture & Storage

### Key Questions to Drive Requirements
1. What patient data views are most critical to capture from Allscripts?
2. What search patterns will RG use most frequently?
3. What reports need to be generated from captured data?
4. How will PHI be protected at rest and in transit?

---

## Technical Constraints
- **Compliance:** HIPAA-compliant storage and handling required
- **Cloud:** Azure ecosystem (existing BAA in place)
- **Language:** TypeScript preferred (per project conventions)
- **Storage:** Azure Blob Storage (encrypted) or local SQLite for Phase 1
- **OCR:** Azure Cognitive Services for screenshot text extraction

---

## Phase 1 Scope (Current Focus)

### In Scope
- Paste/upload screenshots from Allscripts or Athena
- Paste text snippets with patient context
- Tag captures with patient identifiers
- Local encrypted storage OR Azure Blob Storage
- Basic search by patient identifier

### Out of Scope (Future Phases)
- Full EMR functionality
- Direct API integration with Athena/Allscripts
- Care plan report generation
- Multi-user access controls

---

## Project Structure
```
Patient_Explorer/
├── CLAUDE.md              # This file - AI context
├── README.md              # Project overview
├── docs/                  # Requirements, architecture, decisions
├── src/                   # Application code
│   ├── components/        # UI components (if frontend)
│   ├── services/          # Business logic, API clients
│   └── utils/             # Helper functions
└── tests/                 # Test files
```

---

## Working with This Project

### For Requirements Work (Analyst Mode)
- Ask clarifying questions before assuming
- Frame features as user stories: "As a [role], I want [goal] so that [benefit]"
- Include acceptance criteria for each story
- Flag any HIPAA implications explicitly

### For Implementation Work (Developer Mode)
- Follow TypeScript conventions in `.github/copilot-instructions.md`
- Keep functions small and focused
- Add comments for non-obvious clinical domain logic
- Write tests for critical paths

### For Architecture Decisions
- Document in `docs/decisions/` using ADR format
- Consider HIPAA implications for any data handling
- Prefer Azure services where compliance is pre-validated

---

## Current Priority
**Next Step:** Define the core data model for a "Patient Capture" - what fields are needed when RG pastes a screenshot or text snippet?