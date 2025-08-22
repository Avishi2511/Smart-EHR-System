# Complete FHIR Server Setup Guide

This guide will help you set up and run the complete Smart-EHR-System with the custom Python FHIR server.

## What We've Built

✅ **Python FHIR Server** - A complete FHIR R4 compliant server with:
- FastAPI backend with automatic API documentation
- SQLite database (easily upgradeable to PostgreSQL)
- Full CRUD operations for FHIR resources
- Search capabilities with parameters
- CORS enabled for web integration
- Sample data loading scripts

✅ **Smart-EHR-System Integration** - Updated the React frontend to:
- Connect to the local FHIR server instead of remote proxy
- Use real HTTP requests instead of mock data
- Proper error handling for FHIR operations

## Quick Start (5 Minutes)

### Step 1: Start the FHIR Server

```bash
# Navigate to FHIR server directory
cd fhir-server

# Install Python dependencies (first time only)
pip install -r requirements.txt

# Start the FHIR server
python -m app.main
```

The server will start at: **http://localhost:8000**

### Step 2: Load Sample Data

In a new terminal:

```bash
cd fhir-server
python load_sample_data.py
```

This creates sample patients, observations, conditions, encounters, and medications.

### Step 3: Start the React Frontend

In another terminal:

```bash
# From the main project directory
npm install  # (first time only)
npm run dev
```

The React app will start at: **http://localhost:5173**

### Step 4: Verify Everything Works

```bash
cd fhir-server
python test_server.py
```

## What You Can Do Now

### 1. **Explore the FHIR API**
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **FHIR Metadata**: http://localhost:8000/metadata

### 2. **View Patient Data in Smart-EHR-System**
- Open http://localhost:5173
- Browse through the sample patients
- View clinical data (observations, conditions, medications)
- Test the patient summary dashboard

### 3. **Add Your Own Data**

#### Option A: Via API (Programmatic)
```bash
# Create a new patient
curl -X POST http://localhost:8000/Patient \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "name": [{"given": ["Your"], "family": "Name"}],
    "gender": "male",
    "birthDate": "1990-01-01"
  }'
```

#### Option B: Via Python Script
```python
import requests

# Add your patient data
patient_data = {
    "resourceType": "Patient",
    "name": [{"given": ["John"], "family": "Smith"}],
    "gender": "male",
    "birthDate": "1985-03-15",
    "address": [{"city": "Your City", "state": "Your State"}]
}

response = requests.post("http://localhost:8000/Patient", json=patient_data)
print(f"Created patient: {response.json()}")
```

#### Option C: Modify Sample Data
Edit `fhir-server/load_sample_data.py` to include your own data, then run:
```bash
python load_sample_data.py
```

### 4. **Search and Query Data**
```bash
# Search patients by name
curl "http://localhost:8000/Patient?name=John"

# Search observations for a specific patient
curl "http://localhost:8000/Observation?patient=patient-001"

# Get all conditions
curl "http://localhost:8000/Condition"
```

## Supported FHIR Resources

The server currently supports these FHIR resource types:
- **Patient** - Demographics and contact information
- **Observation** - Lab results, vital signs, measurements
- **Condition** - Diagnoses and health problems
- **Encounter** - Hospital visits and appointments
- **MedicationRequest** - Prescriptions and medications
- **Procedure** - Medical procedures and treatments
- **AllergyIntolerance** - Allergies and intolerances
- **Immunization** - Vaccination records

## File Structure

```
Smart-EHR-System/
├── fhir-server/                 # Python FHIR Server
│   ├── app/
│   │   ├── main.py             # FastAPI application
│   │   ├── database.py         # Database configuration
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── crud.py             # Database operations
│   │   └── api/
│   │       └── fhir.py         # FHIR endpoints
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Server configuration
│   ├── load_sample_data.py     # Sample data loader
│   ├── test_server.py          # Server testing script
│   └── README.md               # Detailed server docs
├── src/                        # React Frontend
│   ├── api/
│   │   └── fhirApi.ts          # Updated to use real FHIR server
│   └── ...
├── .env                        # Updated to point to local server
└── FHIR_SETUP_GUIDE.md        # This guide
```

## Next Steps for Development

### 1. **Add More Resource Types**
To support additional FHIR resources:
1. Add the resource import in `app/api/fhir.py`
2. Add it to `SUPPORTED_RESOURCES` dictionary
3. Add search parameters in `app/crud.py`

### 2. **Database Upgrade**
For production, switch to PostgreSQL:
```env
# In fhir-server/.env
DATABASE_URL=postgresql://user:password@localhost:5432/fhir_db
```

### 3. **Add Authentication**
Implement OAuth2 or other authentication mechanisms as needed.

### 4. **Smart Card Integration**
Ready for Phase 2: Add smart card authentication endpoints.

### 5. **RAG Integration**
Ready for Phase 3: Add vector database and AI capabilities.

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   cd fhir-server
   pip install -r requirements.txt
   ```

2. **Port 8000 already in use**
   ```bash
   # Change port in fhir-server/.env
   PORT=8001
   ```

3. **CORS errors in browser**
   - The server is configured for localhost:5173 and localhost:3000
   - Check that both servers are running on correct ports

4. **Database errors**
   - The server uses SQLite by default (no setup required)
   - Database file is created automatically: `fhir-server/fhir.db`

### Getting Help

1. **Check server logs** - Look at the terminal where you started the FHIR server
2. **Test API directly** - Use http://localhost:8000/docs to test endpoints
3. **Verify data** - Run `python test_server.py` to check server status

## Success! 🎉

You now have a complete, working FHIR-based EHR system with:
- ✅ Custom Python FHIR server
- ✅ Real healthcare data storage
- ✅ React frontend integration
- ✅ Sample patient data
- ✅ Full CRUD operations
- ✅ Search capabilities
- ✅ API documentation
- ✅ Ready for extension (smart cards, RAG, etc.)

The foundation is solid and ready for the advanced features you mentioned (smart card integration and RAG capabilities) in future phases!
