# ADNI-Backend Integration Summary

## What Was Implemented

### 1. Unified Pipeline Script (`api/run_pipeline.py`)
- **Auto-detects** unprocessed MRI/PET scans
- **Preprocesses** new scans automatically if found
- **Runs** prediction model with all available data
- **Outputs** clean, constrained scores only (no verbose logging)
- **Sends** results to backend via HTTP POST

### 2. Backend API Endpoint (`backend/app/api/alzheimers.py`)
- **Endpoint**: `POST /api/alzheimers/predictions`
- **Validates** all scores against clinical constraints:
  - MMSE: 0-30
  - CDR-Global: {0, 0.5, 1, 2, 3}
  - CDR-SOB: 0-18
  - ADAS-Cog: 0-70
- **Stores** predictions in memory (can be extended to database)
- **Returns** success/error response

### 3. Clinical Constraints Applied
All predictions use **constrained scores** that follow:
- **Mod difference logic** for MMSE, ADAS-Cog, CDR-SOB
- **Monotonic progression** (scores only increase/decrease appropriately)
- **Scaling** if values exceed valid ranges
- **Categorical mapping** for CDR-Global

## Usage

### Run Pipeline for a Patient
```bash
cd adni-python
python api/run_pipeline.py --patient_id 033S0567
```

### Output Example
```json
{
  "patient_id": "033S0567",
  "last_visit": {
    "date": "20090615",
    "scores": {
      "MMSE": 17.6,
      "CDR_Global": 1.0,
      "CDR_SOB": 7.4,
      "ADAS_Cog": 28.9
    }
  },
  "future_predictions": [
    {
      "months_ahead": 6,
      "scores": {
        "MMSE": 18.8,
        "CDR_Global": 1.0,
        "CDR_SOB": 8.3,
        "ADAS_Cog": 30.5
      }
    }
    // ... 14 more predictions up to 90 months
  ]
}
```

### Backend API Endpoints

#### Store Predictions
```bash
POST http://localhost:3000/api/alzheimers/predictions
Content-Type: application/json

{
  "patient_id": "033S0567",
  "prediction_time": "2025-12-22T13:00:00",
  "last_visit": { ... },
  "future_predictions": [ ... ]
}
```

#### Retrieve Predictions
```bash
GET http://localhost:3000/api/alzheimers/predictions/033S0567
```

#### List All Patients with Predictions
```bash
GET http://localhost:3000/api/alzheimers/predictions
```

## Integration Flow

```
User clicks "Run Model" in Backend
         ↓
Backend triggers: python api/run_pipeline.py --patient_id {id}
         ↓
Pipeline checks for new scans
         ↓
If new scans → Preprocess them
         ↓
Run prediction model
         ↓
Apply clinical constraints (mod difference logic)
         ↓
Output clean JSON with constrained scores
         ↓
HTTP POST to /api/alzheimers/predictions
         ↓
Backend validates and stores predictions
         ↓
Frontend can fetch and display predictions
```

## Files Modified/Created

### Created
- `adni-python/api/run_pipeline.py` - Main orchestration script
- `backend/app/api/alzheimers.py` - API endpoint for predictions

### Modified
- `adni-python/api/clinical_constraints.py` - Added mod difference logic
- `backend/app/main.py` - Registered alzheimers router

## Next Steps

1. **Backend Trigger**: Add button/endpoint in backend to trigger pipeline
2. **Frontend Display**: Create UI to visualize progression graphs
3. **Database Storage**: Replace in-memory storage with SQL database
4. **Error Handling**: Add retry logic and better error messages
5. **Notifications**: Alert users when predictions are ready
