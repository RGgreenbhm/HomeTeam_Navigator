# BETA-003: Alpha Deployment Package

**Priority**: HIGH
**Sprint**: Beta Launch (Dec 3, 2025)
**Owner**: Agent Team (script creation), Jenny (testing)
**Status**: In Progress

---

## User Story

**As a** staff member (Jenny)
**I want to** install Patient Explorer on my Windows computer
**So that** I can help Dr. Green track consent responses during clinic

---

## Acceptance Criteria

### Installation
- [ ] Single PowerShell script handles all setup
- [ ] Works on Windows 11 with Python 3.10+
- [ ] Creates virtual environment automatically
- [ ] Installs all dependencies
- [ ] Creates .env template with prompts
- [ ] Initializes database with default admin user

### Running the App
- [ ] Simple command to start: `.\run-app.ps1`
- [ ] Opens browser to localhost:8501 automatically
- [ ] Shows login page on first run
- [ ] Default credentials documented

### Updates
- [ ] Git pull to update code
- [ ] Re-run setup if dependencies change
- [ ] Database migrations handled gracefully

---

## Technical Implementation

### Prerequisites (Jenny's Machine)
- Windows 11 (BitLocker enabled for HIPAA)
- Python 3.10+ installed and in PATH
- Git installed
- VS Code (optional but recommended)

### Setup Script: `setup-beta.ps1`
```powershell
# Patient Explorer Beta Setup
# Run this script once to configure the application

Write-Host "Patient Explorer Beta Setup" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1
if ($pythonVersion -notmatch "Python 3\.(1[0-9]|[0-9])") {
    Write-Host "ERROR: Python 3.10+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate and install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "IMPORTANT: Edit .env file with your API credentials" -ForegroundColor Red
}

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -c "from app.database import init_db; init_db()"

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file with API credentials"
Write-Host "2. Run: .\run-app.ps1"
Write-Host "3. Login with: admin / admin123"
Write-Host "4. Change the admin password immediately!"
```

### Run Script: `run-app.ps1`
```powershell
# Patient Explorer - Run Application
Write-Host "Starting Patient Explorer..." -ForegroundColor Cyan

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Start Streamlit
streamlit run app/main.py --server.address localhost --server.port 8501
```

### .env.example Template
```env
# Patient Explorer Configuration
# Copy this file to .env and fill in your values

# Spruce Health API (for patient matching)
SPRUCE_API_TOKEN=your_base64_token_here
SPRUCE_ACCESS_ID=your_access_id_here

# Microsoft 365 (optional - for SharePoint/OneNote)
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Microsoft Forms (for consent collection)
MS_FORMS_BASE_URL=https://forms.microsoft.com/r/YOUR_FORM_ID

# Default Admin Password (change after first login!)
DEFAULT_ADMIN_PASSWORD=admin123

# Database (SQLite - no config needed for local)
DATABASE_URL=sqlite:///./patient_explorer.db
```

---

## Deployment Steps for Jenny

### Initial Setup (One Time)

1. **Get the Code**
   ```powershell
   cd C:\Users\Jenny\Projects
   git clone https://github.com/RGgreenbhm/Patient_Explorer.git
   cd Patient_Explorer\Patient_Explorer
   ```

2. **Run Setup**
   ```powershell
   .\setup-beta.ps1
   ```

3. **Configure Credentials**
   - Open `.env` file in Notepad or VS Code
   - Dr. Green will provide Spruce API credentials
   - Save file

4. **Start Application**
   ```powershell
   .\run-app.ps1
   ```

5. **Login**
   - Browser opens to http://localhost:8501
   - Username: `admin`
   - Password: `admin123`
   - Change password in Admin page

### Daily Use

1. Open PowerShell in project folder
2. Run: `.\run-app.ps1`
3. Use app in browser
4. Close PowerShell when done (or Ctrl+C)

### Updates

```powershell
git pull
.\setup-beta.ps1  # Re-run if dependencies changed
.\run-app.ps1
```

---

## Security Notes

- App runs ONLY on localhost (not accessible from network)
- BitLocker must be enabled on machine
- Database file is local only
- Never commit .env file to git
- Change default password immediately

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Python not found | Install Python 3.10+, add to PATH |
| Permission denied | Run PowerShell as Administrator |
| Port 8501 in use | Change port in run-app.ps1 |
| Database error | Delete patient_explorer.db, re-run setup |
| Login fails | Check default password in .env |

---

## Definition of Done

- [ ] setup-beta.ps1 created and tested on dev machine
- [ ] run-app.ps1 created and tested
- [ ] .env.example updated with all required variables
- [ ] Jenny successfully installs on her machine
- [ ] Jenny can login and view dashboard
- [ ] Documentation reviewed by Jenny for clarity

---

*Created: 2025-12-02 by BMAD Agent Team*
