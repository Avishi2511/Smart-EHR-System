# ADNI Pipeline - Quick Reference

## 🚀 Quick Start

### 1. Add Patient Data
```bash
# Create directory structure
mkdir -p api/input_data/patient-002/2024-01-15

# Add files:
# - api/input_data/patient-002/clinical_data.json
# - api/input_data/patient-002/2024-01-15/mri.nii.gz
# - api/input_data/patient-002/2024-01-15/pet.nii.gz
```

### 2. Run Pipeline
```bash
# Option A: All-in-one test
python api/test_pipeline.py --patient_id patient-002

# Option B: Step-by-step
python api/preprocess_patient.py --patient_id patient-002 --session_date 2024-01-15
python api/predict_progression.py --patient_id patient-002
```

---

## 📋 Commands

### Preprocessing
```bash
# First time (6-10 minutes)
python api/preprocess_patient.py --patient_id PATIENT_ID --session_date SESSION_DATE

# Use cached (instant)
python api/preprocess_patient.py --patient_id PATIENT_ID --session_date SESSION_DATE

# Force reprocess
python api/preprocess_patient.py --patient_id PATIENT_ID --session_date SESSION_DATE --force
```

### Prediction
```bash
# Run prediction (2-5 seconds)
python api/predict_progression.py --patient_id PATIENT_ID

# Save to specific file
python api/predict_progression.py --patient_id PATIENT_ID --output predictions/custom.json

# Use GPU (if available)
python api/predict_progression.py --patient_id PATIENT_ID --device cuda
```

### Testing
```bash
# Full test
python api/test_pipeline.py --patient_id PATIENT_ID

# Skip preprocessing (use cached)
python api/test_pipeline.py --patient_id PATIENT_ID --skip-preprocess

# Force reprocess
python api/test_pipeline.py --patient_id PATIENT_ID --force
```

---

## 📁 Directory Structure

```
api/
├── preprocess_patient.py       # Preprocessing script
├── predict_progression.py      # Prediction script
├── test_pipeline.py            # Test script
├── README.md                   # Full documentation
├── PIPELINE_SUMMARY.md         # Summary
├── QUICK_REFERENCE.md          # This file
│
├── input_data/                 # INPUT: Raw data from backend
│   ├── EXAMPLE_clinical_data.json
│   └── {patient_id}/
│       ├── clinical_data.json
│       └── {session_date}/
│           ├── mri.nii.gz
│           └── pet.nii.gz
│
├── preprocessed_data/          # CACHE: Preprocessed features
│   └── {patient_id}/
│       └── {session_date}/
│           ├── mri_brain.nii.gz
│           ├── pet_suvr.nii.gz
│           ├── atlas_in_t1.nii.gz
│           └── roi_features.json  # ⭐ KEY FILE (2 KB)
│
└── predictions/                # OUTPUT: Prediction results
    └── {patient_id}_predictions.json
```

---

## 🔧 Backend Integration

### Python Example
```python
import subprocess
import json

# 1. Preprocess (if new scans)
if new_scans_uploaded:
    subprocess.run([
        "python", "api/preprocess_patient.py",
        "--patient_id", patient_id,
        "--session_date", session_date
    ])

# 2. Predict (always fast)
subprocess.run([
    "python", "api/predict_progression.py",
    "--patient_id", patient_id
])

# 3. Read results
with open(f"api/predictions/{patient_id}_predictions.json") as f:
    predictions = json.load(f)
```

### Node.js Example
```javascript
const { exec } = require('child_process');
const fs = require('fs');

// 1. Preprocess (if new scans)
if (newScansUploaded) {
  exec(`python api/preprocess_patient.py --patient_id ${patientId} --session_date ${sessionDate}`);
}

// 2. Predict
exec(`python api/predict_progression.py --patient_id ${patientId}`, (error, stdout, stderr) => {
  // 3. Read results
  const predictions = JSON.parse(
    fs.readFileSync(`api/predictions/${patientId}_predictions.json`)
  );
});
```

---

## ⏱️ Performance

| Operation | First Time | Cached |
|-----------|-----------|--------|
| Preprocessing | 6-10 min | <1 sec |
| Prediction | 2-5 sec | 2-5 sec |
| **Total** | ~7-12 min | ~3-6 sec |

---

## 🐛 Troubleshooting

### "MRI not found"
```bash
# Check file exists
ls api/input_data/patient-002/2024-01-15/mri.nii.gz

# Check file format (should be NIfTI)
file api/input_data/patient-002/2024-01-15/mri.nii.gz
```

### "Model not found"
```bash
# Check model exists
ls outputs/best_seq_model_FIXED.pt

# If missing, train model first
python code/run_all_seq_FIXED.py
```

### "AAL atlas not found"
```bash
# Check atlas exists
ls atlas/atlases/atlas_aal.nii.gz

# Download if missing (from ADNI or AAL website)
```

### Preprocessing is slow
- Atlas registration takes 3-5 minutes (normal)
- Use cached preprocessing for subsequent runs
- Only use `--force` when necessary

---

## 📊 Output Format

### Prediction JSON
```json
{
  "patient_id": "patient-002",
  "prediction_timestamp": "2024-12-21T23:30:00",
  "sessions": [
    {
      "session_date": "2024-01-15",
      "actual_scores": {
        "MMSE": 24.0,
        "CDR_Global": 0.5,
        "CDR_SOB": 2.5,
        "ADAS_Cog": 12.0
      },
      "predicted_scores": {
        "MMSE": 23.8,
        "CDR_Global": 0.5,
        "CDR_SOB": 2.6,
        "ADAS_Cog": 12.3
      },
      "errors": {
        "MMSE": 0.2,
        "CDR_Global": 0.0,
        "CDR_SOB": 0.1,
        "ADAS_Cog": 0.3
      }
    }
  ],
  "overall_metrics": {
    "mean_absolute_error": 0.15
  }
}
```

---

## 📝 Clinical Data Format

```json
{
  "patient_id": "patient-002",
  "demographics": {
    "date_of_birth": "1948-03-15",
    "gender": "Female",
    "education": 12,
    "apoe_genotype": "3/4"
  },
  "sessions": [
    {
      "session_date": "2024-01-15",
      "age": 76.0,
      "gender": "Female",
      "education": 12,
      "apoe4": 1,
      "mmse_score": 24.0,
      "cdr_global": 0.5,
      "cdr_sob": 2.5,
      "adas_totscore": 12.0
    }
  ]
}
```

**Required fields**:
- `session_date`, `age`, `gender`, `education`, `apoe4`

**Optional fields**:
- `mmse_score`, `cdr_global`, `cdr_sob`, `adas_totscore`

---

## 🎯 Next Steps

1. **Add patient data** to `api/input_data/`
2. **Run test**: `python api/test_pipeline.py --patient_id patient-002`
3. **Verify output** in `api/predictions/`
4. **Integrate with backend** using subprocess or API

---

## 📚 Documentation

- **Full Guide**: `api/README.md`
- **Summary**: `api/PIPELINE_SUMMARY.md`
- **This File**: `api/QUICK_REFERENCE.md`

---

**Ready to test!** 🚀
