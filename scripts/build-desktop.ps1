# Patient Explorer Desktop Build Script
# =====================================
# Builds a distributable Windows desktop application using PyInstaller
#
# Requirements:
#   - Python 3.10+ with virtual environment
#   - PyInstaller (installed automatically)
#   - Windows 11
#
# Usage:
#   .\scripts\build-desktop.ps1
#
# Output:
#   dist\PatientExplorer\  - Complete distributable folder

param(
    [switch]$Clean,      # Clean build directories before building
    [switch]$Debug,      # Build with console window for debugging
    [switch]$SkipInstall # Skip pip install step
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Patient Explorer Desktop Build Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "Project root: $ProjectRoot" -ForegroundColor Gray
Set-Location $ProjectRoot

# Check for virtual environment
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "ERROR: Virtual environment not found at $VenvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
. $ActivateScript

# Install/upgrade PyInstaller
if (-not $SkipInstall) {
    Write-Host "Installing build dependencies..." -ForegroundColor Yellow
    pip install --upgrade pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path ".\build") { Remove-Item -Recurse -Force ".\build" }
    if (Test-Path ".\dist") { Remove-Item -Recurse -Force ".\dist" }
    if (Test-Path ".\PatientExplorer.spec") { Remove-Item -Force ".\PatientExplorer.spec" }
}

# Create build directories
if (-not (Test-Path ".\build")) { New-Item -ItemType Directory -Path ".\build" | Out-Null }
if (-not (Test-Path ".\dist")) { New-Item -ItemType Directory -Path ".\dist" | Out-Null }

# Build configuration
$AppName = "PatientExplorer"
$IconPath = "app\assets\icons\HTnav_medical_bag.png"
$EntryPoint = "scripts\launcher.py"

# Check entry point exists
if (-not (Test-Path $EntryPoint)) {
    Write-Host "ERROR: Entry point not found: $EntryPoint" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build Configuration:" -ForegroundColor Cyan
Write-Host "  App Name: $AppName"
Write-Host "  Entry Point: $EntryPoint"
Write-Host "  Icon: $IconPath"
Write-Host "  Debug Mode: $Debug"
Write-Host ""

# Build PyInstaller command
$PyInstallerArgs = @(
    "--name=$AppName",
    "--onedir",
    "--noconfirm",
    "--clean"
)

# Add icon if exists
if (Test-Path $IconPath) {
    # Note: PyInstaller on Windows prefers .ico files
    # Using PNG may require conversion
    Write-Host "Note: Using PNG icon (consider converting to .ico for best results)" -ForegroundColor Gray
}

# Console or windowed mode
if ($Debug) {
    $PyInstallerArgs += "--console"
    Write-Host "Building with console window (debug mode)" -ForegroundColor Yellow
} else {
    $PyInstallerArgs += "--windowed"
}

# Add data directories
$DataDirs = @(
    "app;app",
    "app\assets;app\assets",
    ".streamlit;.streamlit"
)

foreach ($dir in $DataDirs) {
    $PyInstallerArgs += "--add-data=$dir"
}

# Add hidden imports for Streamlit ecosystem
$HiddenImports = @(
    "streamlit",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.web.cli",
    "altair",
    "pandas",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "plotly",
    "httpx",
    "pydantic",
    "loguru",
    "PIL",
    "openpyxl",
    "xlrd"
)

foreach ($import in $HiddenImports) {
    $PyInstallerArgs += "--hidden-import=$import"
}

# Collect all for key packages
$CollectAll = @(
    "streamlit",
    "altair",
    "plotly"
)

foreach ($pkg in $CollectAll) {
    $PyInstallerArgs += "--collect-all=$pkg"
}

# Add entry point
$PyInstallerArgs += $EntryPoint

Write-Host "Running PyInstaller..." -ForegroundColor Yellow
Write-Host "  pyinstaller $($PyInstallerArgs -join ' ')" -ForegroundColor Gray
Write-Host ""

# Run PyInstaller
& pyinstaller @PyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Post-build setup..." -ForegroundColor Yellow

# Create additional directories in dist
$DistPath = Join-Path $ProjectRoot "dist\$AppName"

# Create data directory
$DataDir = Join-Path $DistPath "data"
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
    Write-Host "  Created: data\" -ForegroundColor Gray
}

# Create logs directory
$LogsDir = Join-Path $DistPath "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-Host "  Created: logs\" -ForegroundColor Gray
}

# Copy .env.example if it exists
$EnvExample = Join-Path $ProjectRoot ".env.example"
if (Test-Path $EnvExample) {
    Copy-Item $EnvExample (Join-Path $DistPath ".env.example")
    Write-Host "  Copied: .env.example" -ForegroundColor Gray
}

# Create README for distribution
$ReadmeContent = @"
PATIENT EXPLORER v1.0
=====================

A HIPAA-compliant patient consent tracking application.

REQUIREMENTS
------------
- Windows 11 Pro or Enterprise
- BitLocker encryption MUST be enabled
- Internet access for API integrations

FIRST-TIME SETUP
----------------
1. Copy your .env file to this folder
   (Obtain API credentials from your IT administrator)

2. Double-click PatientExplorer.exe to start

3. Your browser will open to the application
   (Always runs on localhost:8501 for security)

4. Log in with your Microsoft account or local credentials

SECURITY NOTES
--------------
- All patient data stays on your local encrypted device
- The application only runs on localhost (127.0.0.1)
- External API calls go to HIPAA BAA-covered services only

SUPPORT
-------
- Check logs\ folder for application logs
- Contact your IT administrator for API key issues
- Report bugs at: https://github.com/RGgreenbhm/Patient_Explorer/issues

LICENSE
-------
Proprietary - Home Team Medical Services
"@

$ReadmeContent | Out-File -FilePath (Join-Path $DistPath "README.txt") -Encoding UTF8
Write-Host "  Created: README.txt" -ForegroundColor Gray

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output location: $DistPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "To distribute:" -ForegroundColor Yellow
Write-Host "  1. Add your .env file to the folder"
Write-Host "  2. Zip the entire $AppName folder"
Write-Host "  3. Share the zip file with users"
Write-Host ""
Write-Host "To test locally:" -ForegroundColor Yellow
Write-Host "  .\dist\$AppName\$AppName.exe"
Write-Host ""
