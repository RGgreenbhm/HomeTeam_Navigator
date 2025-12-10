# ADR-001: Beta App Architecture Decisions

**Date:** 2025-12-02
**Status:** Proposed
**Deciders:** Dr. Robert Green, BMAD Team

---

## Context

Patient Explorer needs a beta version deployable to:
1. Dr. Green's development machine
2. Nurse Jenny's workstation (for tomorrow's clinic testing)

The beta must support:
- Microsoft OAuth login (for OneNote access and user authentication)
- Consent tracking workflow
- Spruce API integration
- HIPAA-compliant data handling

---

## Decision 1: Authentication Strategy

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: MS OAuth Only** | Simple, single sign-on, reuses existing MS credentials | Requires Azure app registration |
| **B: Local Auth + MS OAuth** | Works offline, separate concerns | Two auth systems to maintain |
| **C: MS OAuth as Gate, Local Session** | Best of both, MS validates user, local session for speed | Moderate complexity |

### Decision: Option C - MS OAuth as Gate, Local Session

**Rationale:**
- User signs in with Microsoft (southviewteam.com or greenclinicteam.com)
- Microsoft validates identity and provides OneNote access
- Local session created for subsequent requests
- OneNote tokens refreshed as needed

**Implementation:**
```python
# User flow
1. User visits app → Redirected to MS login
2. MS validates credentials + MFA
3. App receives tokens (access + refresh)
4. Create local session with user info
5. Store OneNote tokens for API calls
6. Refresh tokens as needed (daily MFA acceptable)
```

---

## Decision 2: Consent Form Delivery

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: Microsoft Forms** | Quick setup, under existing BAA, familiar to staff | Limited customization, external dependency |
| **B: Custom Streamlit Page** | Full control, integrated, no external dependencies | More development, hosting complexity |
| **C: Hybrid (MS Forms → Streamlit Import)** | Quick start with Forms, import responses to app | Two systems, manual import |

### Decision: Option C - Hybrid Approach

**Rationale:**
- Microsoft Forms for patient-facing consent (quick to set up, HIPAA-compliant under MS BAA)
- Token passed in URL parameter for patient identification
- Responses imported to Patient Explorer via Forms API or CSV export
- Streamlit handles tracking, follow-ups, and reporting

**Implementation:**
1. Create MS Form with consent questions + APCM elections
2. Add hidden field for consent token
3. Share tokenized URL via Spruce SMS
4. Import responses via bulk import feature (already built)

---

## Decision 3: OneNote Integration Architecture

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: Direct Graph API** | Real-time access, full control | Requires OAuth setup, token management |
| **B: SharePoint Sync** | Leverage existing SharePoint client | OneNote on SharePoint has limitations |
| **C: Export → Import** | Simple, no API needed | Manual, not real-time |

### Decision: Option A - Direct Graph API with User Delegation

**Rationale:**
- Microsoft requires delegated auth for OneNote (as of March 2025)
- User signs in, app accesses notebooks user can access
- Aligns with HIPAA minimum necessary principle
- Enables real-time access to Green Clinic Team Notebook

**Implementation:**
```python
# Components needed
1. MicrosoftAuth class (MSAL-based)
2. OneNoteClient class (Graph API wrapper)
3. Streamlit integration (callback handling)
4. Token storage (session-based, not persisted)
```

---

## Decision 4: Alpha Deployment Strategy

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: Local Run Only** | Simple, secure, no hosting | Requires Python/Streamlit knowledge |
| **B: Portable Executable** | No Python needed, USB-deployable | Complex packaging, updates difficult |
| **C: Docker Container** | Consistent environment, easy updates | Docker Desktop required, overhead |
| **D: Batch Script Launcher** | Simple, Python managed, easy to update | Requires Python installation |

### Decision: Option D - Batch Script Launcher with Python

**Rationale:**
- Both machines can have Python installed
- Simple batch script to launch Streamlit
- Updates are git pull + restart
- No complex packaging needed for alpha

**Implementation:**
```batch
@echo off
:: Patient Explorer Alpha Launcher
cd /d "C:\PatientExplorer"
call .venv\Scripts\activate
streamlit run app/main.py --server.port 8501
```

---

## Decision 5: Data Storage

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: SQLite Only** | Simple, portable, no server | Single-user, no sync |
| **B: SQLite + SharePoint Sync** | Offline-capable, cloud backup | Sync complexity |
| **C: Azure SQL** | Cloud-native, multi-user | Cost, complexity, always-online |

### Decision: Option A - SQLite Only (for Alpha)

**Rationale:**
- Alpha is single-user testing
- SQLite with SQLCipher for encryption
- BitLocker provides disk-level encryption
- No cloud sync needed for alpha

**Future:** Implement CouchDB sync for multi-device (Phase 1B)

---

## Decision 6: AI Model Integration

### Options Considered

| Option | Pros | Cons |
|--------|------|------|
| **A: Azure Claude Only** | HIPAA-compliant (under MS BAA), high quality | Cost, requires Azure setup |
| **B: Local Models (Ollama)** | Free, private, no cloud | Lower quality, resource-intensive |
| **C: Hybrid (Azure for PHI, Local for General)** | Cost optimization, privacy for sensitive | Complexity |

### Decision: Option A - Azure Claude Only (for Alpha/Beta)

**Rationale:**
- Azure Foundry Claude is HIPAA-compliant
- Already have Azure configuration
- High quality responses for clinical use
- Can evaluate IBM Granite later

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Patient Explorer Beta                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Streamlit  │    │   SQLite DB  │    │   Azure      │  │
│  │   Frontend   │◄──►│  (encrypted) │    │   Claude     │  │
│  └──────┬───────┘    └──────────────┘    └──────┬───────┘  │
│         │                                        │          │
│  ┌──────▼───────────────────────────────────────▼───────┐  │
│  │                 Integration Layer                      │  │
│  ├──────────────┬───────────────┬────────────────────────┤  │
│  │ MS OAuth     │ Spruce API    │ MS Graph (OneNote)     │  │
│  │ (User Auth)  │ (SMS/Contact) │ (Notebooks)            │  │
│  └──────┬───────┴───────┬───────┴────────────┬───────────┘  │
└─────────┼───────────────┼────────────────────┼──────────────┘
          │               │                    │
    ┌─────▼─────┐   ┌─────▼─────┐        ┌─────▼─────┐
    │ Microsoft │   │  Spruce   │        │ SharePoint│
    │   Entra   │   │  Health   │        │ (OneNote) │
    └───────────┘   └───────────┘        └───────────┘

    ┌─────────────────────────────────────────────────────┐
    │           Patient-Facing (External)                  │
    │  ┌──────────────┐              ┌──────────────────┐ │
    │  │ MS Forms     │              │ SMS (Spruce)     │ │
    │  │ (Consent)    │◄─────────────│ (Tokenized Link) │ │
    │  └──────────────┘              └──────────────────┘ │
    └─────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Week 1 (Dec 2-8)

1. **MS OAuth Integration** - App registration, auth flow
2. **MS Forms Setup** - Create consent form with token field
3. **Spruce SMS Testing** - Validate message sending

### Week 2 (Dec 9-15)

1. **OneNote Integration** - Graph API client, notebook access
2. **End-to-End Testing** - Full consent workflow
3. **Alpha Deployment** - Setup on Jenny's machine

### Week 3 (Dec 16-22)

1. **Bug Fixes** - Address testing feedback
2. **Documentation** - User guides for staff
3. **Pilot Launch** - 50-patient test cohort

### Week 4 (Dec 23-31)

1. **Full Rollout** - All 1,384 patients
2. **Monitoring** - Track consent response rates
3. **Support** - Handle edge cases

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| MS OAuth complexity | High | Use MSAL library, follow documented patterns |
| Spruce rate limits | Medium | Batch SMS in groups of 50 |
| OneNote API deprecation | Low | Already using delegated auth (compliant) |
| Staff adoption | Medium | Simple UI, clear training docs |
| December deadline | Critical | Focus on consent workflow, defer features |

---

## Success Criteria

### Alpha (Tomorrow)
- [ ] App launches on both machines
- [ ] MS login works for Dr. Green
- [ ] Patient list displays
- [ ] Can view consent status

### Beta (Dec 15)
- [ ] Full MS OAuth flow working
- [ ] Consent form submission tracked
- [ ] SMS sending via Spruce
- [ ] OneNote notebook accessible

### Production (Dec 31)
- [ ] All patients imported
- [ ] Consent campaign running
- [ ] Staff trained and using
- [ ] Response tracking accurate

---

*Generated: 2025-12-02 by BMAD Architect Agent*
