# Docker Deployment Proposal for Patient Explorer V1.0

**Date:** December 10, 2025  
**Status:** Proposed  
**Author:** Dr. Green (with GitHub Copilot assistance)

## Executive Summary

This document proposes using Docker to simplify deployment of Patient Explorer V1.0 to staff testers (LaChandra, Lindsay, Jenny). Docker addresses pain points in the current local development approach by providing consistent, reproducible environments across all Windows machines.

### Current State
- Local Streamlit application requiring Python environment setup
- Virtual environment activation and manual dependency installation per machine
- Complex PyInstaller packaging approach outlined in architecture docs

### Proposed State
- Single Docker container running identically on any Windows machine with Docker Desktop
- One-command startup: `docker compose up`
- Volume-mounted data persistence for SQLite database and audit logs

---

## Why Docker for This Project

### Current Deployment Challenges

The existing deployment plan (per `V1-Architecture-Desktop-Deployment.md`) involves:
- PyInstaller packaging (complex, brittle with hidden imports)
- Manual `.venv` activation on each machine
- PowerShell launcher scripts
- Per-machine environment variable configuration

### Docker Benefits

| Challenge | Docker Solution |
|-----------|-----------------|
| Python environment inconsistencies | Container includes exact Python version + all dependencies |
| "Works on my machine" issues | Identical container runs everywhere |
| Complex installation for non-technical staff | Single `docker compose up` command |
| SQLite database portability | Volume mount preserves data between runs |
| Azure credential management | `.env` file injected at runtime |

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAFF WORKSTATION                            │
│                   (Windows 11 + Docker Desktop)                 │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              DOCKER CONTAINER                              │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │ │
│  │  │  Streamlit  │  │   Python    │  │   All Deps      │   │ │
│  │  │   App       │  │   3.10+     │  │  (pre-installed)│   │ │
│  │  │  :8501      │  │             │  │                 │   │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │ │
│  │                         │                                  │ │
│  │                         ▼                                  │ │
│  │              ┌──────────────────────┐                     │ │
│  │              │  Volume Mounts       │                     │ │
│  │              │  • /data (patients.db)                     │ │
│  │              │  • /.env (credentials)                     │ │
│  │              │  • /logs (audit logs)                      │ │
│  │              └──────────────────────┘                     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                         │                                       │
│                         ▼                                       │
│              http://localhost:8501                              │
│                   (Browser Access)                              │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
           ┌──────────────────────────┐
           │   Azure Blob Storage     │
           │   (workspace-sync)       │
           │   (patient-data)         │
           └──────────────────────────┘
```

---

## Required Docker Files

### Files to Create

1. **`Dockerfile`** - Container definition with Python 3.10, all dependencies, Streamlit configuration
2. **`docker-compose.yml`** - Service orchestration with volume mounts and port mapping
3. **`.dockerignore`** - Exclude unnecessary files from build context
4. **`scripts/docker-start.ps1`** - One-click PowerShell launcher for staff
5. **`.env.example`** - Credential template (without actual secrets)

### Distribution Package Structure

```
PatientExplorer-V1.0-Docker/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── requirements.txt
├── app/
├── data/                    # Empty - will hold patients.db
├── logs/                    # Empty - will hold audit logs
├── scripts/
│   └── docker-start.ps1
├── INSTALL.md
└── README.txt
```

---

## Comparison: Docker vs PyInstaller

| Aspect | PyInstaller | Docker |
|--------|-------------|--------|
| Build complexity | High (many hidden imports) | Low (standard Python) |
| Distribution size | ~200MB+ (bundled Python) | ~500MB first pull, then cached |
| Updates | Re-download entire .exe | `docker compose pull` |
| Debugging | Difficult (compiled) | Easy (view logs, attach shell) |
| Cross-machine consistency | Fragile | Guaranteed |
| HIPAA audit trail | Manual log setup | Built-in volume mounts |

---

## Implementation Phases

### Phase 1: Docker Setup (1-2 hours)
- Create `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- Test build locally on development machine
- Verify all 15 Streamlit pages work in container

### Phase 2: Staff Preparation (1 hour)
- Create distribution ZIP
- Write `INSTALL.md` with screenshots
- Pre-configure `.env.example` with placeholder values

### Phase 3: Staff Deployment (2-3 hours)
- Help Jenny install Docker Desktop (test case)
- Validate database sync works across machines
- Document any issues in LESSONS-LEARNED.md

### Phase 4: Shared Testing (ongoing)
- All testers running same container version
- Centralized issue tracking
- Easy updates via `docker compose pull`

---

## Security Considerations

Docker maintains existing HIPAA controls from Security Overview:

- ✅ **BitLocker**: Container runs on encrypted Windows machines
- ✅ **Local-only**: No cloud deployment, localhost access only
- ✅ **Credentials**: `.env` file never baked into image
- ✅ **Audit logs**: Volume-mounted for persistence
- ✅ **Data isolation**: SQLite in mounted volume, not container filesystem

---

## Staff Prerequisites

1. **Windows 11** with admin rights
2. **Docker Desktop** installed (WSL 2 backend)
3. **Credentials** provided by Dr. Green (`.env` file contents)

### Staff Commands

```powershell
# Start the application
.\scripts\docker-start.ps1

# View logs
.\scripts\docker-start.ps1 -Logs

# Stop the application
.\scripts\docker-start.ps1 -Stop

# Rebuild after updates
.\scripts\docker-start.ps1 -Build
```

---

## Recommendation

**Proceed with Docker** as the V1.0 staff deployment method because it is:

1. **Simpler** than PyInstaller for Python/Streamlit stack
2. **More reliable** across different Windows configurations
3. **Easier to update** when fixing bugs during testing
4. **Better documented** in industry (more troubleshooting resources)

---

## Next Steps

- [ ] Create Docker configuration files in repository
- [ ] Test build on development machine
- [ ] Deploy to Jenny's machine as proof-of-concept
- [ ] Iterate based on feedback before full team rollout
- [ ] Update `V1-Architecture-Desktop-Deployment.md` with Docker approach

---

## References

- [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- [Streamlit Docker Deployment](https://docs.streamlit.io/deploy/tutorials/docker)
- Project docs: `V1-Architecture-Desktop-Deployment.md`, `Security Overview.md`
