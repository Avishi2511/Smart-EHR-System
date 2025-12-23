# Load Comprehensive Patient 2 Data to Deployed FHIR Server
# This script creates 118+ observations for Patient 2 (Vimla Bansal)

$fhirServerUrl = "https://smart-ehr-fhir-server.onrender.com"

Write-Host "Loading comprehensive data for Patient 2 (Vimla Bansal)..." -ForegroundColor Cyan
Write-Host "Target FHIR Server: $fhirServerUrl" -ForegroundColor Yellow
Write-Host ""

# First, ensure Patient 2 exists
$patient2 = @{
    resourceType = "Patient"
    id = "2"
    name = @(@{
        given = @("Vimla")
        family = "Bansal"
    })
    gender = "female"
    birthDate = "1955-06-15"
    address = @(@{
        city = "Delhi"
        state = "Delhi"
        postalCode = "110001"
        country = "India"
    })
    telecom = @(@{
        system = "phone"
        value = "+91-98765-43210"
    })
}

Write-Host "Creating/Updating Patient 2..." -NoNewline
try {
    $body = $patient2 | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Uri "$fhirServerUrl/Patient/2" -Method Put -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host " Success" -ForegroundColor Green
}
catch {
    Write-Host " Failed" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Generate comprehensive observations
$observations = @()
$obsId = 1

# Helper function to create observation
function New-Observation {
    param(
        [string]$Type,
        [string]$Code,
        [string]$Display,
        [double]$Value,
        [string]$Unit,
        [string]$Category,
        [datetime]$Date
    )
    
    return @{
        resourceType = "Observation"
        id = "obs-patient2-$script:obsId"
        status = "final"
        category = @(@{
            coding = @(@{
                system = "http://terminology.hl7.org/CodeSystem/observation-category"
                code = $Category
                display = $Category
            })
        })
        code = @{
            coding = @(@{
                system = "http://loinc.org"
                code = $Code
                display = $Display
            })
            text = $Display
        }
        subject = @{
            reference = "Patient/2"
            display = "Vimla Bansal"
        }
        effectiveDateTime = $Date.ToString("yyyy-MM-ddTHH:mm:ssZ")
        valueQuantity = @{
            value = $Value
            unit = $Unit
            system = "http://unitsofmeasure.org"
            code = $Unit
        }
    }
    $script:obsId++
}

Write-Host "Generating observations..." -ForegroundColor Cyan

# Generate lab results over 2 years (every 2 months)
for ($monthsBack = 0; $monthsBack -lt 24; $monthsBack += 2) {
    $date = (Get-Date).AddMonths(-$monthsBack)
    
    # Glucose
    $observations += New-Observation -Type "glucose" -Code "2339-0" -Display "Glucose" `
        -Value (Get-Random -Minimum 90 -Maximum 145) -Unit "mg/dL" -Category "laboratory" -Date $date
    
    # HbA1c
    $observations += New-Observation -Type "hba1c" -Code "4548-4" -Display "HbA1c" `
        -Value ([math]::Round((Get-Random -Minimum 5.5 -Maximum 7.2), 1)) -Unit "%" -Category "laboratory" -Date $date
    
    # Creatinine
    $observations += New-Observation -Type "creatinine" -Code "2160-0" -Display "Creatinine" `
        -Value ([math]::Round((Get-Random -Minimum 0.7 -Maximum 1.2), 1)) -Unit "mg/dL" -Category "laboratory" -Date $date
}

# Generate vital signs (monthly)
for ($monthsBack = 0; $monthsBack -lt 24; $monthsBack++) {
    $date = (Get-Date).AddMonths(-$monthsBack).AddDays((Get-Random -Minimum 0 -Maximum 15))
    
    # Heart Rate
    $observations += New-Observation -Type "heart_rate" -Code "8867-4" -Display "Heart rate" `
        -Value (Get-Random -Minimum 65 -Maximum 85) -Unit "/min" -Category "vital-signs" -Date $date
    
    # Blood Pressure Systolic
    $observations += New-Observation -Type "bp_systolic" -Code "8480-6" -Display "Systolic BP" `
        -Value (Get-Random -Minimum 120 -Maximum 140) -Unit "mmHg" -Category "vital-signs" -Date $date
    
    # Blood Pressure Diastolic
    $observations += New-Observation -Type "bp_diastolic" -Code "8462-4" -Display "Diastolic BP" `
        -Value (Get-Random -Minimum 75 -Maximum 90) -Unit "mmHg" -Category "vital-signs" -Date $date
    
    # Temperature
    $observations += New-Observation -Type "temperature" -Code "8310-5" -Display "Body temperature" `
        -Value ([math]::Round((Get-Random -Minimum 36.5 -Maximum 37.5), 1)) -Unit "Cel" -Category "vital-signs" -Date $date
    
    # Weight
    $observations += New-Observation -Type "weight" -Code "29463-7" -Display "Body Weight" `
        -Value (Get-Random -Minimum 65 -Maximum 72) -Unit "kg" -Category "vital-signs" -Date $date
}

Write-Host "Generated $($observations.Count) observations" -ForegroundColor Green

# Upload observations
$successCount = 0
$failCount = 0

Write-Host ""
Write-Host "Uploading observations to FHIR server..." -ForegroundColor Cyan

foreach ($obs in $observations) {
    try {
        $body = $obs | ConvertTo-Json -Depth 10
        $obsId = $obs.id
        
        Write-Host "  Uploading $obsId..." -NoNewline
        
        $response = Invoke-RestMethod -Uri "$fhirServerUrl/Observation/$obsId" `
            -Method Put `
            -Body $body `
            -ContentType "application/json" `
            -ErrorAction Stop
        
        Write-Host " OK" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host " FAILED" -ForegroundColor Red
        $failCount++
    }
    
    # Small delay to avoid overwhelming the server
    Start-Sleep -Milliseconds 100
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  Successful: $successCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor Red

# Verify
Write-Host ""
Write-Host "Verifying observations for Patient 2..." -ForegroundColor Cyan
try {
    $patientObs = Invoke-RestMethod -Uri "$fhirServerUrl/Observation?subject=Patient/2" -Method Get
    $count = if ($patientObs.entry) { $patientObs.entry.Count } else { 0 }
    Write-Host "Found $count observations for Patient 2" -ForegroundColor Green
}
catch {
    Write-Host "Failed to verify observations" -ForegroundColor Red
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
