# Backend Data Specification for ADNI Pipeline Integration

## Executive Summary

This document specifies **exactly what raw data** the backend needs to provide to the `adni-python` folder for Alzheimer's disease progression prediction. The data will be received from the Smart EHR System's FHIR server and backend, then processed through the ADNI pipeline.

---

## 1. DATA FLOW OVERVIEW

```
FHIR Server (Patient Data)
         ↓
Backend API (Data Aggregation)
         ↓
adni-python/input_data/ (Raw Data Folder)
         ↓
ADNI Pipeline Processing
         ↓
Model Predictions (Cognitive Scores)
```

---

## 2. REQUIRED INPUT DATA STRUCTURE

### 2.1 Folder Structure

The backend should create the following structure in `adni-python/input_data/`:

```
adni-python/
└── input_data/
    ├── imaging/
    │   ├── {patient_id}/
    │   │   ├── {session_date}/
    │   │   │   ├── mri/
    │   │   │   │   └── T1w.nii.gz          # T1-weighted MRI (NIfTI format)
    │   │   │   └── pet/
    │   │   │       └── FDG_pet.nii.gz      # FDG-PET scan (NIfTI format)
    │   │   └── {another_session_date}/
    │   │       └── ...
    │   └── {another_patient_id}/
    │       └── ...
    ├── clinical/
    │   └── clinical_data.csv               # All clinical/demographic data
    └── metadata/
        └── data_manifest.json              # Metadata about the data
```

---

## 3. DETAILED DATA SPECIFICATIONS

### 3.1 Imaging Data (CRITICAL)

#### **A. MRI Scans** (`imaging/{patient_id}/{session_date}/mri/T1w.nii.gz`)

**Format**: NIfTI (.nii.gz)
**Modality**: T1-weighted structural MRI
**Requirements**:
- **Resolution**: Preferably 1mm isotropic (1x1x1mm voxels)
- **Field Strength**: 1.5T or 3T
- **Orientation**: Any (will be reoriented during preprocessing)
- **File Size**: ~10-50 MB compressed
- **Dimensions**: Typically 256x256x170 or similar

**What it contains**:
- 3D brain structural scan
- Shows gray matter, white matter, CSF
- Used to extract regional brain volumes

**Example filename**: `T1w.nii.gz` or `sub-patient002_ses-20240115_T1w.nii.gz`

**How to obtain from FHIR/Backend**:
```python
# From FHIR ImagingStudy resource
{
  "resourceType": "ImagingStudy",
  "id": "imaging-study-001",
  "subject": {"reference": "Patient/patient-002"},
  "started": "2024-01-15T10:00:00Z",
  "series": [{
    "modality": {"code": "MR"},
    "bodySite": {"text": "Brain"},
    "instance": [{
      "sopClass": {"code": "1.2.840.10008.5.1.4.1.1.4"},  # MR Image Storage
      "url": "https://storage.example.com/mri/patient002_20240115_T1.nii.gz"
    }]
  }]
}
```

---

#### **B. PET Scans** (`imaging/{patient_id}/{session_date}/pet/FDG_pet.nii.gz`)

**Format**: NIfTI (.nii.gz)
**Modality**: FDG-PET (Fluorodeoxyglucose Positron Emission Tomography)
**Requirements**:
- **Tracer**: FDG (fluorodeoxyglucose)
- **Dimensions**: Can be 3D or 4D (if 4D, will be averaged)
- **File Size**: ~5-30 MB compressed
- **Co-registration**: Does NOT need to be pre-aligned to MRI (pipeline does this)

**What it contains**:
- 3D brain metabolic activity map
- Shows glucose uptake (brain function)
- Used to detect hypometabolism in AD-affected regions

**Example filename**: `FDG_pet.nii.gz` or `sub-patient002_ses-20240115_pet.nii.gz`

**How to obtain from FHIR/Backend**:
```python
# From FHIR ImagingStudy resource
{
  "resourceType": "ImagingStudy",
  "id": "imaging-study-002",
  "subject": {"reference": "Patient/patient-002"},
  "started": "2024-01-15T11:00:00Z",
  "series": [{
    "modality": {"code": "PT"},  # PET
    "bodySite": {"text": "Brain"},
    "description": "FDG-PET Brain",
    "instance": [{
      "url": "https://storage.example.com/pet/patient002_20240115_FDG.nii.gz"
    }]
  }]
}
```

---

### 3.2 Clinical Data (`clinical/clinical_data.csv`)

**Format**: CSV (Comma-Separated Values)
**Encoding**: UTF-8

#### **Required Columns**:

| Column Name | Data Type | Description | Example | Required? |
|------------|-----------|-------------|---------|-----------|
| `subject_id` | String | Unique patient identifier | `patient-002` | ✅ YES |
| `session_date` | Date | Visit date (YYYY-MM-DD) | `2024-01-15` | ✅ YES |
| `age` | Float | Age at visit (years) | `76.5` | ✅ YES |
| `gender` | String | `Male` or `Female` | `Female` | ✅ YES |
| `education` | Integer | Years of education | `12` | ✅ YES |
| `apoe_genotype` | String | APOE genotype | `3/4` | ⚠️ Recommended |
| `mmse_score` | Float | MMSE score (0-30) | `24.0` | ⚠️ Recommended |
| `cdr_global` | Float | CDR Global (0, 0.5, 1, 2, 3) | `0.5` | ⚠️ Recommended |
| `cdr_sob` | Float | CDR Sum of Boxes (0-18) | `2.5` | ⚠️ Recommended |
| `adas_totscore` | Float | ADAS-Cog Total (0-70) | `12.0` | ⚠️ Recommended |
| `diagnosis` | String | Clinical diagnosis | `MCI` | ⚠️ Optional |
| `has_mri` | Boolean | MRI available? | `true` | ✅ YES |
| `has_pet` | Boolean | PET available? | `true` | ✅ YES |

#### **Example CSV Content**:

```csv
subject_id,session_date,age,gender,education,apoe_genotype,mmse_score,cdr_global,cdr_sob,adas_totscore,diagnosis,has_mri,has_pet
patient-002,2015-06-15,67.5,Female,12,3/4,28.0,0.0,0.0,8.5,CN,true,true
patient-002,2016-01-10,68.1,Female,12,3/4,27.0,0.5,1.0,10.2,MCI,true,true
patient-002,2016-07-15,68.6,Female,12,3/4,26.0,0.5,1.5,12.0,MCI,true,true
patient-002,2017-01-20,69.1,Female,12,3/4,25.0,0.5,2.0,14.5,MCI,true,true
patient-002,2017-07-25,69.6,Female,12,3/4,24.0,1.0,3.0,18.0,Mild AD,true,true
patient-002,2018-01-30,70.1,Female,12,3/4,23.0,1.0,3.5,20.5,Mild AD,true,true
patient-002,2018-08-05,70.6,Female,12,3/4,22.0,1.0,4.0,23.0,Mild AD,true,true
patient-002,2019-02-10,71.1,Female,12,3/4,21.0,1.0,4.5,25.5,Mild AD,true,true
patient-002,2019-08-15,71.6,Female,12,3/4,20.0,1.5,5.5,28.0,Moderate AD,true,true
patient-002,2020-02-20,72.1,Female,12,3/4,19.0,1.5,6.0,30.5,Moderate AD,true,true
```

---

### 3.3 Metadata (`metadata/data_manifest.json`)

**Format**: JSON
**Purpose**: Track data completeness and quality

```json
{
  "data_version": "1.0",
  "generated_at": "2024-12-21T15:00:00Z",
  "total_patients": 1,
  "total_sessions": 10,
  "patients": [
    {
      "patient_id": "patient-002",
      "name": "Vimla Bansal",
      "date_of_birth": "1948-03-15",
      "baseline_date": "2015-06-15",
      "total_visits": 10,
      "visits": [
        {
          "session_date": "2015-06-15",
          "age": 67.5,
          "has_mri": true,
          "has_pet": true,
          "has_cognitive_scores": true,
          "mri_path": "imaging/patient-002/2015-06-15/mri/T1w.nii.gz",
          "pet_path": "imaging/patient-002/2015-06-15/pet/FDG_pet.nii.gz",
          "data_quality": {
            "mri_file_size_mb": 25.3,
            "pet_file_size_mb": 12.7,
            "mri_dimensions": [256, 256, 170],
            "pet_dimensions": [128, 128, 63],
            "complete": true
          }
        },
        {
          "session_date": "2016-01-10",
          "age": 68.1,
          "has_mri": true,
          "has_pet": true,
          "has_cognitive_scores": true,
          "mri_path": "imaging/patient-002/2016-01-10/mri/T1w.nii.gz",
          "pet_path": "imaging/patient-002/2016-01-10/pet/FDG_pet.nii.gz",
          "data_quality": {
            "complete": true
          }
        }
      ]
    }
  ],
  "data_completeness": {
    "sessions_with_mri": 10,
    "sessions_with_pet": 10,
    "sessions_with_both": 10,
    "sessions_with_cognitive_scores": 10,
    "complete_sessions": 10
  }
}
```

---

## 4. DATA EXTRACTION FROM FHIR SERVER

### 4.1 Patient Demographics

**FHIR Resource**: `Patient`

```python
# Example FHIR Patient resource
{
  "resourceType": "Patient",
  "id": "patient-002",
  "name": [{"given": ["Vimla"], "family": "Bansal"}],
  "gender": "female",
  "birthDate": "1948-03-15",
  "extension": [
    {
      "url": "http://example.org/fhir/StructureDefinition/education",
      "valueInteger": 12
    },
    {
      "url": "http://example.org/fhir/StructureDefinition/apoe-genotype",
      "valueString": "3/4"
    }
  ]
}
```

**Extract**:
- `gender` → `gender` (convert to "Male"/"Female")
- `birthDate` → Calculate `age` at each visit
- `extension[education]` → `education`
- `extension[apoe-genotype]` → `apoe_genotype`

---

### 4.2 Cognitive Assessments

**FHIR Resource**: `Observation`

#### **MMSE Score**:
```python
{
  "resourceType": "Observation",
  "id": "obs-mmse-001",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "72106-8",
      "display": "Mini-Mental State Examination"
    }],
    "text": "MMSE"
  },
  "subject": {"reference": "Patient/patient-002"},
  "effectiveDateTime": "2024-01-15T10:00:00Z",
  "valueQuantity": {
    "value": 24.0,
    "unit": "score"
  }
}
```

#### **CDR Scores**:
```python
{
  "resourceType": "Observation",
  "id": "obs-cdr-001",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "52493-4",
      "display": "Clinical Dementia Rating"
    }]
  },
  "subject": {"reference": "Patient/patient-002"},
  "effectiveDateTime": "2024-01-15T10:00:00Z",
  "component": [
    {
      "code": {"text": "CDR Global"},
      "valueQuantity": {"value": 0.5}
    },
    {
      "code": {"text": "CDR Sum of Boxes"},
      "valueQuantity": {"value": 2.5}
    }
  ]
}
```

#### **ADAS-Cog Score**:
```python
{
  "resourceType": "Observation",
  "id": "obs-adas-001",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "54629-3",
      "display": "ADAS-Cog Total Score"
    }]
  },
  "subject": {"reference": "Patient/patient-002"},
  "effectiveDateTime": "2024-01-15T10:00:00Z",
  "valueQuantity": {
    "value": 12.0,
    "unit": "score"
  }
}
```

---

### 4.3 Diagnosis

**FHIR Resource**: `Condition`

```python
{
  "resourceType": "Condition",
  "id": "condition-002-alzheimers",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "26929004",
      "display": "Alzheimer's disease"
    }],
    "text": "Mild Cognitive Impairment"
  },
  "subject": {"reference": "Patient/patient-002"},
  "clinicalStatus": {"coding": [{"code": "active"}]},
  "onsetDateTime": "2016-01-10",
  "stage": [{
    "summary": {"text": "MCI"}
  }]
}
```

**Extract**:
- `stage.summary.text` → `diagnosis` (CN, MCI, Mild AD, Moderate AD, Severe AD)

---

### 4.4 Imaging Studies

**FHIR Resource**: `ImagingStudy`

```python
{
  "resourceType": "ImagingStudy",
  "id": "imaging-study-002-mri",
  "status": "available",
  "subject": {"reference": "Patient/patient-002"},
  "started": "2024-01-15T10:00:00Z",
  "modality": [{"code": "MR"}],
  "series": [{
    "uid": "1.2.840.113619.2.55.3.123456789.1",
    "modality": {"code": "MR"},
    "description": "T1-weighted 3D MPRAGE",
    "bodySite": {"text": "Brain"},
    "instance": [{
      "uid": "1.2.840.113619.2.55.3.123456789.1.1",
      "sopClass": {
        "system": "urn:ietf:rfc:3986",
        "code": "1.2.840.10008.5.1.4.1.1.4"
      },
      "number": 1,
      "title": "T1w Brain MRI",
      "extension": [{
        "url": "http://example.org/fhir/StructureDefinition/nifti-url",
        "valueUrl": "https://storage.example.com/imaging/patient-002/2024-01-15/mri/T1w.nii.gz"
      }]
    }]
  }]
}
```

**Extract**:
- Download NIfTI file from `extension[nifti-url].valueUrl`
- Save to `imaging/{patient_id}/{session_date}/mri/T1w.nii.gz`

---

## 5. BACKEND API ENDPOINT SPECIFICATION

### 5.1 Proposed API Endpoint

```python
POST /api/v1/adni/prepare-patient-data
```

**Request Body**:
```json
{
  "patient_id": "patient-002",
  "include_historical": true,
  "start_date": "2015-01-01",
  "end_date": "2024-12-31"
}
```

**Response**:
```json
{
  "status": "success",
  "patient_id": "patient-002",
  "data_prepared": true,
  "output_directory": "adni-python/input_data/",
  "summary": {
    "total_visits": 10,
    "visits_with_mri": 10,
    "visits_with_pet": 10,
    "visits_with_cognitive_scores": 10,
    "complete_visits": 10
  },
  "files_created": [
    "imaging/patient-002/2015-06-15/mri/T1w.nii.gz",
    "imaging/patient-002/2015-06-15/pet/FDG_pet.nii.gz",
    "clinical/clinical_data.csv",
    "metadata/data_manifest.json"
  ],
  "ready_for_processing": true
}
```

---

### 5.2 Backend Implementation Pseudocode

```python
async def prepare_adni_patient_data(patient_id: str):
    """
    Prepare patient data for ADNI pipeline processing.
    """
    # 1. Create output directories
    base_dir = Path("adni-python/input_data")
    imaging_dir = base_dir / "imaging" / patient_id
    clinical_dir = base_dir / "clinical"
    metadata_dir = base_dir / "metadata"
    
    for dir in [imaging_dir, clinical_dir, metadata_dir]:
        dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Fetch patient demographics from FHIR
    patient = await fhir_client.get(f"Patient/{patient_id}")
    demographics = extract_demographics(patient)
    
    # 3. Fetch all imaging studies for patient
    imaging_studies = await fhir_client.search(
        "ImagingStudy",
        params={"patient": patient_id}
    )
    
    # 4. Fetch all cognitive assessments
    observations = await fhir_client.search(
        "Observation",
        params={
            "patient": patient_id,
            "code": "72106-8,52493-4,54629-3"  # MMSE, CDR, ADAS-Cog
        }
    )
    
    # 5. Fetch diagnosis/conditions
    conditions = await fhir_client.search(
        "Condition",
        params={"patient": patient_id}
    )
    
    # 6. Download imaging files
    clinical_rows = []
    visits = {}
    
    for study in imaging_studies:
        session_date = study["started"][:10]  # YYYY-MM-DD
        session_dir = imaging_dir / session_date
        
        # Download MRI
        mri_url = extract_nifti_url(study, modality="MR")
        if mri_url:
            mri_path = session_dir / "mri" / "T1w.nii.gz"
            mri_path.parent.mkdir(parents=True, exist_ok=True)
            await download_file(mri_url, mri_path)
            has_mri = True
        else:
            has_mri = False
        
        # Download PET
        pet_url = extract_nifti_url(study, modality="PT")
        if pet_url:
            pet_path = session_dir / "pet" / "FDG_pet.nii.gz"
            pet_path.parent.mkdir(parents=True, exist_ok=True)
            await download_file(pet_url, pet_path)
            has_pet = True
        else:
            has_pet = False
        
        # Get cognitive scores for this date
        scores = get_scores_for_date(observations, session_date)
        diagnosis = get_diagnosis_for_date(conditions, session_date)
        
        # Calculate age at visit
        age = calculate_age(demographics["birthDate"], session_date)
        
        # Build clinical data row
        clinical_rows.append({
            "subject_id": patient_id,
            "session_date": session_date,
            "age": age,
            "gender": demographics["gender"],
            "education": demographics.get("education", ""),
            "apoe_genotype": demographics.get("apoe_genotype", ""),
            "mmse_score": scores.get("mmse", ""),
            "cdr_global": scores.get("cdr_global", ""),
            "cdr_sob": scores.get("cdr_sob", ""),
            "adas_totscore": scores.get("adas", ""),
            "diagnosis": diagnosis,
            "has_mri": has_mri,
            "has_pet": has_pet
        })
        
        visits[session_date] = {
            "has_mri": has_mri,
            "has_pet": has_pet,
            "has_scores": bool(scores)
        }
    
    # 7. Write clinical data CSV
    df = pd.DataFrame(clinical_rows)
    df = df.sort_values("session_date")
    df.to_csv(clinical_dir / "clinical_data.csv", index=False)
    
    # 8. Write metadata manifest
    manifest = {
        "data_version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "patient_id": patient_id,
        "total_visits": len(visits),
        "visits": visits
    }
    with open(metadata_dir / "data_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    
    return {
        "status": "success",
        "total_visits": len(visits),
        "ready_for_processing": all(
            v["has_mri"] and v["has_pet"] 
            for v in visits.values()
        )
    }
```

---

## 6. DATA QUALITY REQUIREMENTS

### 6.1 Imaging Data Quality

**MRI Requirements**:
- ✅ Must be T1-weighted structural scan
- ✅ Must cover whole brain
- ✅ Minimum resolution: 1mm isotropic (preferred)
- ✅ No severe motion artifacts
- ✅ Proper DICOM → NIfTI conversion

**PET Requirements**:
- ✅ Must be FDG-PET (not other tracers)
- ✅ Must cover whole brain
- ✅ Can be 3D or 4D (will be averaged)
- ✅ Proper DICOM → NIfTI conversion

### 6.2 Clinical Data Quality

**Required for Each Visit**:
- ✅ Valid patient ID
- ✅ Valid session date
- ✅ Age (calculated or provided)
- ✅ Gender
- ✅ Education years

**Recommended for Each Visit**:
- ⚠️ At least one cognitive score (MMSE, CDR, or ADAS-Cog)
- ⚠️ APOE genotype (can be same for all visits)
- ⚠️ Diagnosis/stage

### 6.3 Temporal Requirements

**For Progression Modeling**:
- ✅ Minimum 2 visits (baseline + 1 follow-up)
- ✅ Recommended: 3+ visits over 6-12 months
- ✅ Visits should be chronologically ordered
- ✅ Baseline visit should have complete data

---

## 7. EXAMPLE: COMPLETE DATA PACKAGE

### 7.1 For Patient "Vimla Bansal" (patient-002)

**Folder Structure**:
```
adni-python/input_data/
├── imaging/
│   └── patient-002/
│       ├── 2015-06-15/
│       │   ├── mri/T1w.nii.gz (25.3 MB)
│       │   └── pet/FDG_pet.nii.gz (12.7 MB)
│       ├── 2016-01-10/
│       │   ├── mri/T1w.nii.gz
│       │   └── pet/FDG_pet.nii.gz
│       ├── 2016-07-15/
│       │   ├── mri/T1w.nii.gz
│       │   └── pet/FDG_pet.nii.gz
│       └── ... (7 more visits)
├── clinical/
│   └── clinical_data.csv (10 rows, 12 columns)
└── metadata/
    └── data_manifest.json
```

**clinical_data.csv** (first 3 rows):
```csv
subject_id,session_date,age,gender,education,apoe_genotype,mmse_score,cdr_global,cdr_sob,adas_totscore,diagnosis,has_mri,has_pet
patient-002,2015-06-15,67.5,Female,12,3/4,28.0,0.0,0.0,8.5,CN,true,true
patient-002,2016-01-10,68.1,Female,12,3/4,27.0,0.5,1.0,10.2,MCI,true,true
patient-002,2016-07-15,68.6,Female,12,3/4,26.0,0.5,1.5,12.0,MCI,true,true
```

**Total Data Size**: ~400 MB (10 visits × ~40 MB per visit)

---

## 8. VALIDATION CHECKLIST

Before processing, the backend should validate:

- [ ] Patient ID exists in FHIR server
- [ ] At least 2 visits with imaging data
- [ ] All MRI files are valid NIfTI format
- [ ] All PET files are valid NIfTI format
- [ ] MRI and PET files are not corrupted
- [ ] Clinical CSV has all required columns
- [ ] No missing values in required fields
- [ ] Dates are in correct format (YYYY-MM-DD)
- [ ] Age values are reasonable (0-120)
- [ ] Cognitive scores are in valid ranges:
  - MMSE: 0-30
  - CDR Global: 0, 0.5, 1, 2, 3
  - CDR SOB: 0-18
  - ADAS-Cog: 0-70
- [ ] Gender is "Male" or "Female"
- [ ] Education is positive integer
- [ ] APOE genotype is valid (e.g., "3/3", "3/4", "4/4")

---

## 9. ERROR HANDLING

### 9.1 Missing Data Scenarios

| Scenario | Action |
|----------|--------|
| No MRI for a visit | Skip that visit (pipeline requires both MRI and PET) |
| No PET for a visit | Skip that visit |
| Missing cognitive scores | Include visit (model can handle missing scores) |
| Missing APOE genotype | Use default value or mark as unknown |
| Missing education | Use population average (12 years) |

### 9.2 Data Quality Issues

| Issue | Action |
|-------|--------|
| Corrupted NIfTI file | Log error, skip visit, notify admin |
| Invalid date format | Attempt to parse, or skip visit |
| Out-of-range scores | Log warning, use as-is (model may handle) |
| Duplicate visits | Keep most recent (by upload time) |

---

## 10. SUMMARY: MINIMUM VIABLE DATA

**For a single patient to be processed**:

1. **Demographics** (one-time):
   - Patient ID
   - Date of birth (or age at baseline)
   - Gender
   - Education years

2. **Imaging** (per visit, minimum 2 visits):
   - T1-weighted MRI (NIfTI format)
   - FDG-PET scan (NIfTI format)

3. **Clinical** (per visit):
   - Visit date
   - At least one cognitive score (MMSE, CDR, or ADAS-Cog)

**Recommended Additional Data**:
- APOE genotype
- All 4 cognitive scores (MMSE, CDR-Global, CDR-SOB, ADAS-Cog)
- Diagnosis/stage
- Multiple visits (3-10) over time for better progression modeling

---

## 11. NEXT STEPS

1. **Backend Team**: Implement `/api/v1/adni/prepare-patient-data` endpoint
2. **FHIR Team**: Ensure imaging URLs are accessible and NIfTI files are available
3. **Data Team**: Validate existing patient data against this specification
4. **Pipeline Team**: Create data ingestion script to read from `input_data/` folder
5. **Testing**: Test with Vimla Bansal (patient-002) as pilot case

---

## APPENDIX A: FHIR to CSV Mapping

| FHIR Resource | FHIR Field | CSV Column | Transformation |
|---------------|------------|------------|----------------|
| Patient | `id` | `subject_id` | Direct copy |
| Patient | `birthDate` | `age` | Calculate from visit date |
| Patient | `gender` | `gender` | Capitalize first letter |
| Patient | `extension[education]` | `education` | Extract integer |
| Patient | `extension[apoe]` | `apoe_genotype` | Extract string |
| Observation (MMSE) | `valueQuantity.value` | `mmse_score` | Extract float |
| Observation (CDR) | `component[0].valueQuantity.value` | `cdr_global` | Extract float |
| Observation (CDR) | `component[1].valueQuantity.value` | `cdr_sob` | Extract float |
| Observation (ADAS) | `valueQuantity.value` | `adas_totscore` | Extract float |
| Condition | `stage.summary.text` | `diagnosis` | Extract text |
| ImagingStudy | `started` | `session_date` | Extract date (YYYY-MM-DD) |
| ImagingStudy (MR) | `instance.extension[nifti-url]` | N/A | Download to `imaging/.../mri/` |
| ImagingStudy (PT) | `instance.extension[nifti-url]` | N/A | Download to `imaging/.../pet/` |

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-21  
**Author**: Smart EHR System - ADNI Integration Team
