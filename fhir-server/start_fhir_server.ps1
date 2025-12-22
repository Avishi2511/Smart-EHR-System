# Start FHIR Server with Virtual Environment
# This script activates the virtual environment and starts the FHIR server

Write-Host "🚀 Starting FHIR Server..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& .\venv_fhir\Scripts\Activate.ps1

# Check if activation was successful
if ($LASTEXITCODE -eq 0 -or $env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
    Write-Host ""
    
    # Start the server
    Write-Host "🌐 Starting FHIR server on http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Write-Host ""
    
    python -m app.main
} else {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    Write-Host "Please make sure venv_fhir exists and is properly set up" -ForegroundColor Yellow
    exit 1
}
