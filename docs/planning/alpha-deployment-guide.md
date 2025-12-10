# Alpha Deployment Guide

**Version:** Alpha 0.1
**Date:** 2025-12-02
**Target:** Dr. Green's machine + Nurse Jenny's workstation

---

## Overview

This guide covers deploying Patient Explorer alpha for testing during tomorrow's clinic session.

---

## Prerequisites

### Both Machines Need:
- Windows 10/11 with BitLocker enabled
- Python 3.10+ installed
- Git installed
- Network access (for Spruce API, MS OAuth)
- Microsoft account (southviewteam.com or greenclinicteam.com)

### Check Python Installation
```cmd
python --version
# Should show Python 3.10 or higher
```

### Check Git Installation
```cmd
git --version
```

---

## Installation Steps

### Step 1: Clone Repository

```cmd
cd C:\
git clone https://github.com/RGgreenbhm/Patient_Explorer.git
cd Patient_Explorer\Patient_Explorer
```

### Step 2: Create Virtual Environment

```cmd
python -m venv .venv
```

### Step 3: Activate Virtual Environment

```cmd
.venv\Scripts\activate
```

### Step 4: Install Dependencies

```cmd
pip install -r requirements.txt
```

### Step 5: Configure Environment

Copy the example environment file and edit with real credentials:

```cmd
copy .env.example .env
notepad .env
```

Required settings:
```env
# Spruce Health API
SPRUCE_API_TOKEN=<get from Dr. Green>
SPRUCE_ACCESS_ID=<get from Dr. Green>

# Microsoft OAuth (after app registration)
MS_CLIENT_ID=<from Azure Portal>
MS_CLIENT_SECRET=<from Azure Portal>
MS_TENANT_ID=southviewteam.com
MS_REDIRECT_URI=http://localhost:8501/callback

# Azure Claude (optional for alpha)
AZURE_CLAUDE_ENDPOINT=<if available>
AZURE_CLAUDE_API_KEY=<if available>

# Consent Form URL (after MS Forms setup)
MS_CONSENT_FORM_URL=<from Microsoft Forms>
```

### Step 6: Initialize Database

```cmd
python -m phase0 init-db
```

### Step 7: Launch Application

```cmd
streamlit run app/main.py
```

Application will open at: http://localhost:8501

---

## Quick Start Launcher

Create a launcher script for easy startup:

### File: `start-patient-explorer.bat`
```batch
@echo off
echo Starting Patient Explorer Alpha...
cd /d "C:\Patient_Explorer\Patient_Explorer"
call .venv\Scripts\activate
streamlit run app/main.py --server.port 8501 --browser.gatherUsageStats false
```

Save this file to desktop for quick access.

---

## Jenny's Machine Setup

### Option A: Full Installation
Follow all steps above on Jenny's machine.

### Option B: Network Share (Same Network)
If both machines are on same network:

1. Dr. Green runs: `streamlit run app/main.py --server.address 0.0.0.0 --server.port 8501`
2. Jenny accesses: `http://<dr-green-ip>:8501`

Note: This requires firewall exception for port 8501.

### Option C: USB Transfer
1. Copy entire `Patient_Explorer` folder to USB
2. Transfer to Jenny's machine
3. Run installation steps 2-7

---

## First Run Checklist

### On Each Machine:

1. [ ] Launch application
2. [ ] Verify home page loads
3. [ ] Check patient list displays (if data imported)
4. [ ] Test Spruce connection (if credentials configured)
5. [ ] Attempt Microsoft login (if OAuth configured)

### Common Issues:

| Issue | Solution |
|-------|----------|
| Port 8501 in use | Use `--server.port 8502` |
| Module not found | Re-run `pip install -r requirements.txt` |
| Database error | Delete `data/patients.db` and re-init |
| Spruce error | Verify API credentials in .env |

---

## Testing Workflow (Tomorrow's Clinic)

### Morning Setup (Dr. Green)
1. Launch Patient Explorer
2. Sign in with Microsoft
3. Verify patient list loaded
4. Test consent token generation

### During Clinic (Jenny)
1. Open Patient Explorer on her machine
2. View patient list
3. Test consent tracking updates
4. Note any issues for later fix

### After Clinic
1. Review issues list
2. Prioritize fixes
3. Update for next session

---

## Data Import (If Needed)

### Import Patient Excel
1. Go to Patient List page
2. Click "Import All Data"
3. Select Excel file from `data/` folder
4. Wait for Spruce matching
5. Verify patient count

### Generate Consent Tokens
1. Go to Outreach Campaign page
2. Click "Generate Tokens" tab
3. Select patients without tokens
4. Click "Generate"

---

## Troubleshooting

### Application Won't Start
```cmd
# Check if port is in use
netstat -ano | findstr 8501

# Kill process if needed
taskkill /PID <process_id> /F

# Try different port
streamlit run app/main.py --server.port 8502
```

### Database Locked
```cmd
# Close all Python processes
taskkill /IM python.exe /F

# Restart application
```

### Module Import Errors
```cmd
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Microsoft Login Fails
- Verify MS_CLIENT_ID and MS_CLIENT_SECRET in .env
- Check redirect URI matches Azure app registration
- Ensure admin consent granted for permissions

---

## Security Notes

### BitLocker
Both machines should have BitLocker enabled:
```cmd
manage-bde -status C:
```

### Screen Lock
Set automatic screen lock after 5 minutes of inactivity.

### Network
- Prefer wired connection over WiFi
- Avoid public WiFi for PHI access

---

## Support

### During Alpha Testing
- Dr. Green: Primary contact for issues
- Claude Code: Available for debugging assistance

### Issue Reporting
Note any issues in:
`..Workspace_Focus/2025-12-02_SessionPlanner.md` > Section 5

Format:
```
| Issue | Steps to Reproduce | Priority |
|-------|-------------------|----------|
| ... | ... | HIGH/MEDIUM/LOW |
```

---

## Next Steps After Alpha

1. **Document Issues** - All bugs and UX problems
2. **Prioritize Fixes** - Critical vs nice-to-have
3. **Beta Planning** - What's needed for full rollout
4. **Staff Training** - Guide for LaChandra, Lindsay

---

*Created: 2025-12-02 by BMAD Team*
