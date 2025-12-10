# clone-to-hometeam.ps1
# Clone Patient_Explorer to HomeTeam_Navigator without PHI
# Run from D:\Projects folder

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     CLONE PATIENT_EXPLORER TO HOMETEAM_NAVIGATOR             ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║ Source: D:\Projects\Patient_Explorer                         ║" -ForegroundColor White
Write-Host "║ Target: D:\Projects\HomeTeam_Navigator                       ║" -ForegroundColor White
Write-Host "║ GitHub: RGgreenbhm/HomeTeam_Navigator                        ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check we're in the right place
if (-not (Test-Path "D:\Projects")) {
    Write-Host "ERROR: D:\Projects folder not found" -ForegroundColor Red
    exit 1
}

Set-Location "D:\Projects"

# Check source exists
if (-not (Test-Path "Patient_Explorer")) {
    Write-Host "ERROR: Patient_Explorer not found in D:\Projects" -ForegroundColor Red
    exit 1
}

# Check target doesn't exist
if (Test-Path "HomeTeam_Navigator") {
    Write-Host "WARNING: HomeTeam_Navigator already exists!" -ForegroundColor Yellow
    $confirm = Read-Host "Delete and recreate? (yes/no)"
    if ($confirm -eq "yes") {
        Remove-Item -Recurse -Force "HomeTeam_Navigator"
    } else {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

if ($DryRun) {
    Write-Host "[DRY RUN] Would perform the following actions:" -ForegroundColor Yellow
    Write-Host "  1. Clone Patient_Explorer to HomeTeam_Navigator" -ForegroundColor Gray
    Write-Host "  2. Remove .git folder" -ForegroundColor Gray
    Write-Host "  3. Remove data/* (PHI)" -ForegroundColor Gray
    Write-Host "  4. Remove .env (credentials)" -ForegroundColor Gray
    Write-Host "  5. Remove logs/*" -ForegroundColor Gray
    Write-Host "  6. Remove backup_* folders" -ForegroundColor Gray
    Write-Host "  7. Remove SyncLogs (Green Clinic specific)" -ForegroundColor Gray
    Write-Host "  8. Initialize fresh git repo" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "Step 1: Cloning repository structure..." -ForegroundColor Green

# Clone shallow copy
git clone --depth 1 https://github.com/RGgreenbhm/Patient_Explorer.git HomeTeam_Navigator
Set-Location "HomeTeam_Navigator"

Write-Host "Step 2: Removing git history..." -ForegroundColor Green
Remove-Item -Recurse -Force .git

Write-Host "Step 3: Removing PHI and sensitive data..." -ForegroundColor Green

# Remove PHI
if (Test-Path "data") {
    Get-ChildItem "data" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "  - Cleared data/ folder" -ForegroundColor Gray
}

# Remove credentials
if (Test-Path ".env") {
    Remove-Item -Force ".env"
    Write-Host "  - Removed .env" -ForegroundColor Gray
}

# Remove logs
if (Test-Path "logs") {
    Get-ChildItem "logs" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "  - Cleared logs/ folder" -ForegroundColor Gray
}

# Remove backups
Get-ChildItem -Directory -Filter "backup_*" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Write-Host "  - Removed backup_* folders" -ForegroundColor Gray

# Remove Green Clinic specific sync logs
$syncLogsPath = "..Workspace\History\SyncLogs"
if (Test-Path $syncLogsPath) {
    Get-ChildItem $syncLogsPath -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "  - Cleared SyncLogs (Green Clinic specific)" -ForegroundColor Gray
}

Write-Host "Step 4: Creating empty folder structure..." -ForegroundColor Green

# Ensure data folder exists with .gitkeep
New-Item -ItemType Directory -Path "data" -Force | Out-Null
New-Item -ItemType File -Path "data\.gitkeep" -Force | Out-Null

# Ensure logs folder exists with .gitkeep
New-Item -ItemType Directory -Path "logs" -Force | Out-Null
New-Item -ItemType File -Path "logs\.gitkeep" -Force | Out-Null

Write-Host "Step 5: Creating .env.template for Home Team..." -ForegroundColor Green

$envTemplate = @"
# HomeTeam_Navigator Environment Configuration
# Domain: hometeammed.com
# Created: $(Get-Date -Format "yyyy-MM-dd")

# =============================================================================
# SPRUCE HEALTH API (Home Team account)
# =============================================================================
SPRUCE_API_TOKEN=<your_home_team_spruce_token>
SPRUCE_ACCESS_ID=<your_home_team_access_id>

# =============================================================================
# AZURE STORAGE (Home Team workspace)
# =============================================================================
AZURE_STORAGE_ACCOUNT=sthometeamworkspace
AZURE_TENANT_ID=<hometeammed_tenant_id>

# =============================================================================
# MICROSOFT 365 (Home Team tenant)
# =============================================================================
MS_CLIENT_ID=<home_team_client_id>
MS_TENANT_ID=<hometeammed_tenant_id>

# =============================================================================
# INBOUND DATA SOURCES
# =============================================================================
# Monitor this email for patient record transfers from Green Clinic
INBOUND_EMAIL=info@hometeammed.com
INBOUND_EMAIL_MONITOR=true

# =============================================================================
# CROSS-REFERENCE SETTINGS
# =============================================================================
# Enable cross-referencing with Green Clinic patient records
CROSS_REF_ENABLED=true
CROSS_REF_SOURCE_ORG=Green Clinic
CROSS_REF_IDENTIFIER=green_clinic_mrn

# =============================================================================
# PATHS
# =============================================================================
PATIENT_DATA_PATH=data/
LOG_FILE=logs/hometeam_navigator.log
"@

$envTemplate | Out-File -FilePath ".env.template" -Encoding UTF8
Write-Host "  - Created .env.template" -ForegroundColor Gray

Write-Host "Step 6: Initializing fresh git repository..." -ForegroundColor Green
git init
git remote add origin https://github.com/RGgreenbhm/HomeTeam_Navigator.git

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    CLONE COMPLETE                            ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║ Location: D:\Projects\HomeTeam_Navigator                     ║" -ForegroundColor White
Write-Host "╠══════════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║ NEXT STEPS:                                                  ║" -ForegroundColor Yellow
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 1. Create GitHub repo: RGgreenbhm/HomeTeam_Navigator         ║" -ForegroundColor White
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 2. Grant Claude Code access to new repo:                     ║" -ForegroundColor White
Write-Host "║    https://github.com/settings/installations                 ║" -ForegroundColor Cyan
Write-Host "║    → Configure Claude Code → Add HomeTeam_Navigator          ║" -ForegroundColor Cyan
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 3. Copy .env.template to .env and fill in values             ║" -ForegroundColor White
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 4. Update CLAUDE.md and .gitignore-sync.json                 ║" -ForegroundColor White
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 5. Create Azure resources for hometeammed.com                ║" -ForegroundColor White
Write-Host "║                                                              ║" -ForegroundColor Yellow
Write-Host "║ 6. Initial commit and push:                                  ║" -ForegroundColor White
Write-Host "║    git add -A                                                ║" -ForegroundColor Cyan
Write-Host "║    git commit -m 'Initial HomeTeam_Navigator deployment'     ║" -ForegroundColor Cyan
Write-Host "║    git push -u origin main                                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "REMINDER: Monitor info@hometeammed.com for Green Clinic transfers" -ForegroundColor Magenta
