# Quick Start Guide - Smart EHR Backend
This guide will help you get the Smart EHR Backend up and running in 5 minutes.
## Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- FHIR server running on http://localhost:8000 (optional for testing)
## Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```
**Note**: First installation will take a few minutes as it downloads:
- PyTorch (~200MB)
- Sentence Transformers model (~90MB)
- Other dependencies
## Step 2: Configure Environment
The `.env` file is already created with default settings. You can modify it if needed:
```bash
# Edit .env if you need to change:
# - FHIR server URL
# - Port number
# - File storage paths
```
## Step 3: Start the Backend
```bash
python -m app.main
```
You should see:
```
INFO:     Starting Smart EHR Backend...
INFO:     Initializing database...
INFO:     ✓ FHIR server connection successful
INFO:     ✓ Vector database initialized
INFO:     Smart EHR Backend started successfully!
INFO:     Uvicorn running on http://0.0.0.0:8001
```
## Step 4: Verify Installation
Open your browser and visit:
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
Or run the test script:
```bash
python test_backend.py
```
## Step 5: Try It Out!
### Create a Patient
```bash
curl -X POST http://localhost:8001/api/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "fhir_id": "patient-001",
    "nfc_card_id": "card-001",
    "first_name": "John",
    "last_name": "Doe",
    "gender": "male"
  }'
```
### Run a Disease Model
```bash
curl -X POST http://localhost:8001/api/models/execute \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "<patient-id-from-above>",
    "model_name": "diabetes_risk",
    "override_parameters": {
      "age": 65,
      "bmi": 27.5,
      "glucose": 110,
      "hba1c": 6.2,
      "systolic_bp": 135,
      "family_history_diabetes": 1
    }
  }'
```
### Upload a File
```bash
curl -X POST http://localhost:8001/api/files/upload \
  -F "patient_id=<patient-id>" \
  -F "category=lab_report" \
  -F "file=@/path/to/document.pdf"
```
## What's Next?
1. **Explore the API**: Visit http://localhost:8001/docs for interactive API documentation
2. **Read the README**: See `README.md` for detailed API documentation
3. **Check Architecture**: See `ARCHITECTURE.md` for system design details
4. **Add Disease Models**: Follow the guide in README to add custom models
## Common Issues
### Port Already in Use
If port 8001 is already in use, change it in `.env`:
```bash
PORT=8002
```
### FHIR Server Not Running
If you don't have a FHIR server, the backend will still work but won't be able to fetch FHIR data. You can:
- Start the FHIR server: `cd fhir-server && python -m app.main`
- Or ignore FHIR warnings and use manual parameters
### Tesseract Not Found (for OCR)
If you want to extract text from images, install Tesseract:
**Windows**:
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```
**Linux**:
```bash
sudo apt-get install tesseract-ocr
```
**macOS**:
```bash
brew install tesseract
```
## Background File Processing (Optional)
To automatically process uploaded files in the background:
```bash
# In a separate terminal
python -m app.workers.file_worker
```
This worker will continuously check for unprocessed files and embed them.
## Stopping the Backend
Press `Ctrl+C` in the terminal where the backend is running.
## Next Steps
- Integrate with the frontend
- Add custom disease models
- Upload patient documents
- Run predictive models
- Query patient data with natural language
For more details, see the full [README.md](README.md).
