@echo off
echo.
echo ========================================
echo   Starting FHIR Server
echo ========================================
echo.

echo Activating virtual environment...
call venv_fhir\Scripts\activate.bat

if errorlevel 1 (
    echo.
    echo ERROR: Failed to activate virtual environment
    echo Please make sure venv_fhir exists and is properly set up
    pause
    exit /b 1
)

echo Virtual environment activated successfully!
echo.
echo Starting FHIR server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

python -m app.main
