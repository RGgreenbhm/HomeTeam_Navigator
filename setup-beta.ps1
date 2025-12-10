# Patient Explorer Beta Setup
# Run this script once to configure the application
# Usage: .\setup-beta.ps1

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Patient Explorer Beta Setup         " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.(1[0-9]|[0-9])") {
        Write-Host "[OK] $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Python 3.10+ required. Found: $pythonVersion" -ForegroundColor Red
        Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    exit 1
}

# Create virtual environment if needed
if (-not (Test-Path ".venv")) {
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & ".\.venv\Scripts\Activate.ps1"
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Create .env if not exists
Write-Host ""
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "[CREATED] .env file from template" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "  IMPORTANT: Configure .env file!      " -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Open .env in a text editor and add your API credentials:" -ForegroundColor Yellow
        Write-Host "  - SPRUCE_API_TOKEN" -ForegroundColor White
        Write-Host "  - SPRUCE_ACCESS_ID" -ForegroundColor White
        Write-Host "  - MS_FORMS_BASE_URL (after creating form)" -ForegroundColor White
    } else {
        Write-Host "[WARNING] .env.example not found - you'll need to create .env manually" -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] .env file exists" -ForegroundColor Green
}

# Initialize database
Write-Host ""
Write-Host "Initializing database..." -ForegroundColor Yellow
try {
    python -c "import sys; sys.path.insert(0, 'app'); from database import init_db; init_db()"
    Write-Host "[OK] Database initialized" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] Database initialization may have issues - will retry on first run" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Setup Complete!                     " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env file with your API credentials" -ForegroundColor White
Write-Host "  2. Run: .\run-app.ps1" -ForegroundColor White
Write-Host "  3. Login with: admin / admin123" -ForegroundColor White
Write-Host "  4. CHANGE THE PASSWORD in Admin settings!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Questions? Contact Dr. Green or check docs/stories/" -ForegroundColor Gray
Write-Host ""
