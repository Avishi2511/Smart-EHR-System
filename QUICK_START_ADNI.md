# Quick Start Guide - ADNI Model Integration

## Current Status

You have TWO backends that need DIFFERENT Python environments:
1. **FHIR Server** (`fhir-server/`) - Port 8000 - Requires Pydantic v1.x
2. **ADNI Backend** (`backend/`) - Port 8001 - Requires Pydantic v2.7+

## Solution: Use Separate Virtual Environments

### Step 1: Set Up ADNI Backend (Port 8001)

```powershell
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv_adni

# Activate it
.\venv_adni\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend
python -m app.main
```

The backend should start on **http://localhost:8001**

### Step 2: Set Up FHIR Server (Port 8000) - In a NEW Terminal

```powershell
# Navigate to fhir-server directory
cd fhir-server

# Create a separate virtual environment
python -m venv venv_fhir

# Activate it
.\venv_fhir\Scripts\activate

# Install dependencies (with Pydantic v1)
pip install -r requirements.txt

# Start the FHIR server
python -m app.main
```

The FHIR server should start on **http://localhost:8000**

### Step 3: Restart Frontend

The frontend already has the proxy configured. Just restart it:

```powershell
# In the root directory
# Stop current npm start (Ctrl+C)
npm start
```

### Step 4: Test the ADNI Model

1. Navigate to: `http://localhost:5173/app/adni-model`
2. Select a patient
3. Click "Run ADNI Progression Model"
4. View the results!

## Current Configuration

- **Frontend**: `http://localhost:5173` (Vite dev server)
- **ADNI Backend**: `http://localhost:8001` (FastAPI - ADNI models)
- **FHIR Server**: `http://localhost:8000` (FastAPI - FHIR resources)

The frontend proxy forwards `/api/*` requests to `http://localhost:8001`

## Troubleshooting

### If Backend Won't Start

**Error**: `ModuleNotFoundError: No module named 'pydantic._internal'`
**Solution**: Make sure you're in the correct virtual environment with Pydantic 2.7.4

```powershell
cd backend
.\venv_adni\Scripts\activate
pip install pydantic==2.7.4 pydantic-settings==2.1.0
```

### If FHIR Server Won't Start

**Error**: `ImportError: cannot import name 'ROOT_VALIDATOR_CONFIG_KEY'`
**Solution**: Make sure you're in the FHIR virtual environment with Pydantic 1.x

```powershell
cd fhir-server
.\venv_fhir\Scripts\activate
pip install "pydantic<2.0"
```

### If Frontend Shows 404

**Solution**: 
1. Make sure the ADNI backend is running on port 8001
2. Restart the frontend dev server to pick up the proxy configuration
3. Check browser console for errors

## Files Modified

1. `vite.config.ts` - Added proxy configuration
2. `src/App.tsx` - Added ADNI model route
3. `src/layout/Sidebar/SideBar.tsx` - Added navigation link
4. `src/layout/SidebarMobile/SideBarMobile.tsx` - Added mobile navigation
5. `src/pages/ADNIModel/ADNIModelPageWrapper.tsx` - Created wrapper component
6. `src/components/ADNIModelPage.tsx` - Fixed TypeScript errors
7. `backend/app/models/schemas.py` - Added missing schemas
8. `backend/requirements.txt` - Updated Pydantic version

## Next Steps

Once both backends are running:
1. Load sample data into FHIR server
2. Create a test patient
3. Run the ADNI model
4. View the timeline visualization

## Important Notes

- Always activate the correct virtual environment before starting each backend
- The two backends CANNOT share the same Python environment due to Pydantic version conflicts
- Keep both backends running in separate terminal windows
