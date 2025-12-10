# Patient Explorer - Run Application
# Usage: .\run-app.ps1

Write-Host ""
Write-Host "Starting Patient Explorer..." -ForegroundColor Cyan
Write-Host ""

# Check if .venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run setup-beta.ps1 first: .\setup-beta.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host "The app may not function correctly without API credentials." -ForegroundColor Yellow
    Write-Host "Copy .env.example to .env and configure it." -ForegroundColor Yellow
    Write-Host ""
}

# Activate virtual environment
try {
    & ".\.venv\Scripts\Activate.ps1"
} catch {
    Write-Host "[ERROR] Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Start Streamlit
Write-Host "Opening browser to http://localhost:8501" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the application" -ForegroundColor Gray
Write-Host ""

# Run Streamlit
streamlit run app/main.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false
