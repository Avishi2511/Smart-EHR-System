# ADNI Prediction API - Local Pipeline

## Overview

This is a **local, laptop-based pipeline** for Alzheimer's disease progression prediction. It consists of two main scripts:

1. **`preprocess_patient.py`** - Preprocesses raw MRI/PET scans
2. **`predict_progression.py`** - Runs trained model to predict future cognitive scores

---

## Quick Start

### 1. Prepare Input Data

Create the following directory structure in `api/input_data/`:

```
api/input_data/
└── {patient_id}/
    ├── clinical_data.json          # Patient demographics and scores
    └── {session_date}/
        ├── mri.nii.gz              # Raw T1-weighted MRI scan
        └── pet.nii.gz              # Raw FDG-PET scan
```

**Example**: For patient `patient-002` with session on `2024-01-15`:

```
api/input_data/
└── patient-002/
    ├── clinical_data.json
    └── 2024-01-15/
        ├── mri.nii.gz
        └── pet.nii.gz
```

---

### 2. Clinical Data Format

`clinical_data.json` should contain:

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

**Required fields per session**:
- `session_date` (YYYY-MM-DD)
- `age` (years)
- `gender` ("Male" or "Female")
- `education` (years)
- `apoe4` (0, 1, or 2 - number of APOE4 alleles)

**Optional fields** (cognitive scores):
- `mmse_score` (0-30)
- `cdr_global` (0, 0.5, 1, 2, 3)
- `cdr_sob` (0-18)
- `adas_totscore` (0-70)

---

### 3. Run Preprocessing

```bash
python api/preprocess_patient.py --patient_id patient-002 --session_date 2024-01-15
```

**What it does**:
1. N4 bias correction (~2 min)
2. Brain extraction (~3 min)
3. PET registration (~1 min)
4. SUVR normalization (~30 sec)
5. Atlas registration (~5 min) ⚠️ **SLOWEST STEP**
6. ROI feature extraction (~30 sec)

**Total time**: ~6-10 minutes per session

**Output**:
```
api/preprocessed_data/
└── patient-002/
    └── 2024-01-15/
        ├── mri_brain.nii.gz        # Preprocessed MRI
        ├── pet_suvr.nii.gz         # SUVR-normalized PET
        ├── atlas_in_t1.nii.gz      # Registered atlas
        ├── brain_mask.nii.gz       # Brain mask
        └── roi_features.json       # ⭐ EXTRACTED FEATURES (2 KB)
```

**Caching**: If you run preprocessing again for the same session, it will use cached features (instant).

---

### 4. Run Prediction

```bash
python api/predict_progression.py --patient_id patient-002
```

**What it does**:
1. Loads trained model (`best_seq_model_FIXED.pt`)
2. Loads preprocessed ROI features (from `roi_features.json`)
3. Loads clinical data
4. Runs LSTM inference (~2-5 seconds)
5. Outputs predictions

**Output**:
```
api/predictions/
└── patient-002_predictions.json
```

**Terminal output**:
```
================================================================================
PREDICTION RESULTS
================================================================================

Patient ID: patient-002
Prediction Time: 2024-12-21T23:30:00
Number of Sessions: 1

Session         Score        Actual     Predicted  Error     
--------------------------------------------------------------------------------
2024-01-15      MMSE         24.0       23.8       0.20      
2024-01-15      CDR_Global   0.5        0.5        0.00      
2024-01-15      CDR_SOB      2.5        2.6        0.10      
2024-01-15      ADAS_Cog     12.0       12.3       0.30      

================================================================================
Overall Metrics:
  Mean Absolute Error: 0.150
  Median Absolute Error: 0.150
================================================================================
```

---

## Workflow

### First Time (New Patient/Session)

```bash
# 1. Add input data
#    - Copy MRI and PET to api/input_data/{patient_id}/{session_date}/
#    - Create clinical_data.json

# 2. Preprocess (takes 6-10 minutes)
python api/preprocess_patient.py --patient_id patient-002 --session_date 2024-01-15

# 3. Predict (takes 2-5 seconds)
python api/predict_progression.py --patient_id patient-002
```

### Subsequent Runs (Cached Preprocessing)

```bash
# If no new MRI/PET uploaded, preprocessing uses cache (instant)
python api/preprocess_patient.py --patient_id patient-002 --session_date 2024-01-15
# Output: "✓ Preprocessed data already exists. Loading cached features..."

# Prediction (always fast, 2-5 seconds)
python api/predict_progression.py --patient_id patient-002
```

### Force Reprocessing

```bash
# If you want to reprocess even with cached data
python api/preprocess_patient.py --patient_id patient-002 --session_date 2024-01-15 --force
```

---

## Backend Integration

### Input from Backend

Backend should provide:

1. **Raw imaging files**: MRI and PET NIfTI files
2. **Clinical data**: JSON with demographics and cognitive scores
3. **Change flag**: Whether new scans were uploaded

**Example backend API call**:
```python
# Backend sends data to local pipeline
import subprocess
import json

# 1. Save files to input directory
# (backend handles file transfer)

# 2. Check if preprocessing needed
if new_scans_uploaded:
    # Run preprocessing
    result = subprocess.run([
        "python", "api/preprocess_patient.py",
        "--patient_id", patient_id,
        "--session_date", session_date
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Preprocessing failed:", result.stderr)
        exit(1)

# 3. Run prediction (always fast)
result = subprocess.run([
    "python", "api/predict_progression.py",
    "--patient_id", patient_id,
    "--output", f"predictions/{patient_id}.json"
], capture_output=True, text=True)

# 4. Read predictions
with open(f"predictions/{patient_id}.json", 'r') as f:
    predictions = json.load(f)

# 5. Send to backend
# (backend handles API response)
```

### Output to Backend

Prediction script outputs JSON:

```json
{
  "patient_id": "patient-002",
  "prediction_timestamp": "2024-12-21T23:30:00",
  "model_version": "best_seq_model_FIXED.pt",
  "num_sessions": 1,
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
    "mean_absolute_error": 0.15,
    "median_absolute_error": 0.15
  }
}
```

---

## Performance

### Preprocessing (First Time)
- **Time**: 6-10 minutes per session
- **Bottleneck**: Atlas registration (SyN, 3-5 min)
- **Output**: Cached features (2 KB JSON)

### Preprocessing (Cached)
- **Time**: <1 second
- **Action**: Loads cached `roi_features.json`

### Prediction
- **Time**: 2-5 seconds
- **Action**: Model inference on preprocessed features

---

## Directory Structure

```
adni-python/
├── api/
│   ├── preprocess_patient.py       # Preprocessing script
│   ├── predict_progression.py      # Prediction script
│   ├── README.md                   # This file
│   ├── input_data/                 # Raw input from backend
│   │   └── {patient_id}/
│   │       ├── clinical_data.json
│   │       └── {session_date}/
│   │           ├── mri.nii.gz
│   │           └── pet.nii.gz
│   ├── preprocessed_data/          # Cached preprocessed features
│   │   └── {patient_id}/
│   │       └── {session_date}/
│   │           ├── mri_brain.nii.gz
│   │           ├── pet_suvr.nii.gz
│   │           ├── atlas_in_t1.nii.gz
│   │           └── roi_features.json  # ⭐ KEY FILE
│   └── predictions/                # Prediction outputs
│       └── {patient_id}_predictions.json
├── code/                           # Original preprocessing code
├── outputs/
│   └── best_seq_model_FIXED.pt     # Trained model
└── atlas/                          # AAL atlas and MNI template
```

---

## Troubleshooting

### Error: "MRI not found"
- Check that MRI file exists at `api/input_data/{patient_id}/{session_date}/mri.nii.gz`
- Ensure file is in NIfTI format (.nii or .nii.gz)

### Error: "Model not found"
- Ensure `outputs/best_seq_model_FIXED.pt` exists
- If not, train the model first using `code/run_all_seq_FIXED.py`

### Error: "AAL atlas not found"
- Check that `atlas/atlases/atlas_aal.nii.gz` exists
- Download from ADNI or AAL website if missing

### Preprocessing is slow
- Atlas registration takes 3-5 minutes (normal)
- Use `--force` flag only when necessary
- Cached preprocessing is instant

---

## Next Steps

1. **Add your patient data** to `api/input_data/`
2. **Run preprocessing** for each session
3. **Run prediction** to get results
4. **Integrate with backend** using subprocess or API calls

---

## Notes

- **Caching**: Preprocessing results are cached. Only reprocess if new scans uploaded.
- **Model**: Uses `best_seq_model_FIXED.pt` (trained LSTM with temporal derivatives)
- **Features**: 193 dimensions (93 MRI + 93 PET + 7 demographics)
- **Targets**: 4 cognitive scores (MMSE, CDR-Global, CDR-SOB, ADAS-Cog)
