# ADNI Model Integration - Quick Setup Guide

## Installation Steps

### 1. Install Frontend Dependencies

```bash
npm install recharts
npm install --save-dev @types/recharts
```

### 2. Verify Backend Dependencies

Backend dependencies are already in `requirements.txt`:
- ✅ torch==2.1.2
- ✅ numpy==1.26.3
- ✅ fastapi==0.109.0
- ✅ sqlalchemy==2.0.25

### 3. Start Backend

```bash
cd backend
python -m app.main
```

Expected output:
```
INFO:     Starting Smart EHR Backend...
INFO:     Initializing database...
INFO:     ADNI model loaded successfully
INFO:     ✓ FHIR server connection successful
INFO:     ✓ Vector database initialized
INFO:     Smart EHR Backend started successfully!
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 4. Start Frontend

```bash
npm run dev
```

### 5. Test the Integration

1. Navigate to patient page
2. Import and use the ADNI component:

```tsx
import ADNIModelPage from './components/ADNIModelPage';

function PatientPage() {
  const patientId = "your-patient-id";
  
  return (
    <div>
      <h1>Patient Dashboard</h1>
      <ADNIModelPage patientId={patientId} />
    </div>
  );
}
```

3. Click "Run ADNI Progression Model"
4. View the timeline visualization

## Quick Test

### Create Test Patient

```bash
curl -X POST http://localhost:8001/api/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "fhir_id": "test-adni-001",
    "first_name": "John",
    "last_name": "Doe",
    "gender": "male"
  }'
```

### Run ADNI Model

```bash
curl -X POST http://localhost:8001/api/models/execute \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "<patient-id-from-above>",
    "model_name": "adni_progression"
  }'
```

## Troubleshooting

### Issue: "Module 'recharts' not found"
**Solution**: `npm install recharts`

### Issue: "Cannot import ModelFillingLSTM"
**Solution**: Ensure `adni_python/code/` is in the correct location

### Issue: "Model file not found"
**Solution**: Check `adni_python/outputs/best_seq_model_FIXED.pt` exists

### Issue: CORS error
**Solution**: Add frontend URL to `CORS_ORIGINS` in backend `.env`

## File Checklist

Backend:
- [x] `app/services/adni_model_service.py`
- [x] `app/services/adni_parameter_mapper.py`
- [x] `app/services/model_runner.py` (updated)
- [x] `app/models/schemas.py` (updated)

Frontend:
- [x] `src/components/ADNIModelPage.tsx`
- [x] `src/components/ADNIModelPage.css`

Model:
- [x] `adni_python/code/run_all_seq_FIXED.py`
- [x] `adni_python/outputs/best_seq_model_FIXED.pt`

## Success Indicators

✅ Backend starts without errors  
✅ ADNI model loads successfully  
✅ Frontend compiles without errors  
✅ "Run Model" button appears on page  
✅ Clicking button triggers API call  
✅ Timeline charts render with data  
✅ Risk level badge displays correctly  

## Next Steps

1. Test with real patient data
2. Verify predictions are reasonable
3. Customize styling as needed
4. Add to main navigation
5. Deploy to production

---

**Ready to use!** 🎉
