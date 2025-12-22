# ADNI Processing Pipeline: Optimization Strategy

## Executive Summary

This document outlines an **optimized two-stage processing pipeline** that minimizes prediction time by pre-computing expensive preprocessing steps and storing intermediate results. The strategy reduces prediction time from **~15-20 minutes to ~30-60 seconds**.

---

## 1. CURRENT PIPELINE (Unoptimized)

### 1.1 Full Processing Timeline

```
Patient Request → Download Images → Preprocess → Extract ROI → Model Prediction
                  (30s)              (5-10min)    (10-15min)   (5-10s)
                  
TOTAL TIME: ~15-20 minutes per patient
```

### 1.2 Time Breakdown

| Stage | Task | Time | Bottleneck? |
|-------|------|------|-------------|
| 1 | Download MRI from cloud | ~15s | ❌ Network |
| 2 | Download PET from cloud | ~15s | ❌ Network |
| 3 | N4 bias correction (MRI) | ~2-3min | ✅ **YES** |
| 4 | Brain extraction (MRI) | ~3-5min | ✅ **YES** (SyN registration) |
| 5 | PET averaging (if 4D) | ~10s | ❌ |
| 6 | PET → T1 registration | ~1-2min | ⚠️ Moderate |
| 7 | SUVR normalization | ~30s | ❌ |
| 8 | Atlas registration (MNI → T1) | ~5-10min | ✅ **YES** (SyN registration) |
| 9 | ROI feature extraction | ~30s | ❌ |
| 10 | Model inference | ~5-10s | ❌ |

**Total**: ~15-20 minutes

**Key Bottlenecks**:
1. **Brain extraction** (3-5 min) - SyN registration to MNI
2. **Atlas registration** (5-10 min) - SyN registration to subject space
3. **N4 bias correction** (2-3 min) - Iterative algorithm

---

## 2. OPTIMIZED TWO-STAGE PIPELINE

### 2.1 Strategy Overview

**Key Insight**: Preprocessing is **patient-specific but visit-independent** for structural steps. We can pre-compute and cache intermediate results.

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: OFFLINE PREPROCESSING (Run once per scan upload)  │
│ Time: 15-20 minutes (async, background job)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    [Store in Cloud]
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: ONLINE PREDICTION (Run on-demand)                 │
│ Time: 30-60 seconds (real-time)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. STAGE 1: OFFLINE PREPROCESSING (Background Job)

### 3.1 When to Run

**Trigger**: Immediately after imaging scan is uploaded to FHIR server

**Execution**: Asynchronous background job (Celery, RabbitMQ, or similar)

**Frequency**: Once per imaging session (never needs to be repeated)

### 3.2 Processing Steps

```python
# STAGE 1: Offline Preprocessing Pipeline
# Triggered by: POST /ImagingStudy (FHIR upload)
# Execution: Background worker
# Time: 15-20 minutes

def offline_preprocessing_pipeline(imaging_study_id):
    """
    Pre-compute expensive preprocessing steps and store results.
    """
    # 1. Download raw images from cloud
    mri_raw = download_from_cloud(imaging_study.mri_url)  # 15s
    pet_raw = download_from_cloud(imaging_study.pet_url)  # 15s
    
    # 2. MRI Preprocessing (EXPENSIVE)
    mri_n4 = n4_bias_correction(mri_raw)                  # 2-3min ⚠️
    mri_brain, brain_mask = brain_extraction(mri_n4)      # 3-5min ⚠️
    
    # 3. PET Preprocessing
    pet_avg = average_if_4d(pet_raw)                      # 10s
    pet_in_t1 = register_pet_to_t1(pet_avg, mri_brain)    # 1-2min ⚠️
    
    # 4. Cerebellar mask for SUVR
    cereb_mask = warp_cereb_mask_to_t1(mri_brain)         # 1-2min ⚠️
    
    # 5. SUVR normalization
    pet_suvr = compute_suvr(pet_in_t1, cereb_mask)        # 30s
    
    # 6. Atlas Registration (MOST EXPENSIVE)
    aal_atlas_in_t1 = register_atlas_to_t1(mri_brain)     # 5-10min ⚠️⚠️⚠️
    
    # 7. ROI Feature Extraction
    mri_roi_features = extract_roi_features(mri_brain, aal_atlas_in_t1)  # 30s
    pet_roi_features = extract_roi_features(pet_suvr, aal_atlas_in_t1)   # 30s
    
    # 8. Store preprocessed outputs in cloud storage
    storage_path = f"preprocessed/{patient_id}/{session_date}/"
    
    outputs = {
        # Preprocessed images (for quality control)
        "mri_brain": mri_brain,              # ~25 MB
        "pet_suvr": pet_suvr,                # ~12 MB
        "brain_mask": brain_mask,            # ~5 MB
        "atlas_in_t1": aal_atlas_in_t1,      # ~10 MB
        
        # Extracted features (MOST IMPORTANT)
        "mri_roi_features": mri_roi_features,  # 93 floats = ~1 KB
        "pet_roi_features": pet_roi_features,  # 93 floats = ~1 KB
        
        # Metadata
        "preprocessing_timestamp": datetime.now(),
        "preprocessing_version": "1.0",
        "quality_metrics": compute_qc_metrics(mri_brain, pet_suvr)
    }
    
    # Upload to cloud storage
    upload_to_cloud(storage_path, outputs)
    
    # Update FHIR ImagingStudy with preprocessing status
    update_fhir_imaging_study(imaging_study_id, {
        "extension": [{
            "url": "preprocessing-status",
            "valueCode": "completed"
        }, {
            "url": "preprocessed-features-url",
            "valueUrl": f"{storage_path}/roi_features.json"
        }]
    })
    
    return {
        "status": "completed",
        "processing_time_seconds": 900,  # ~15 minutes
        "features_url": f"{storage_path}/roi_features.json"
    }
```

### 3.3 What to Store

**Option A: Store Everything (Recommended for Quality Control)**
```
preprocessed/{patient_id}/{session_date}/
├── mri_brain.nii.gz           # 25 MB - Preprocessed MRI
├── pet_suvr.nii.gz            # 12 MB - SUVR-normalized PET
├── brain_mask.nii.gz          # 5 MB  - Brain mask
├── atlas_in_t1.nii.gz         # 10 MB - Registered atlas
├── roi_features.json          # 2 KB  - ⭐ MOST IMPORTANT
├── preprocessing_log.json     # 1 KB  - Metadata
└── quality_metrics.json       # 1 KB  - QC metrics
```
**Total**: ~52 MB per session

**Option B: Store Only Features (Minimal Storage)**
```
preprocessed/{patient_id}/{session_date}/
└── roi_features.json          # 2 KB - Only the extracted features
```
**Total**: ~2 KB per session

**Recommended**: **Option A** - Store everything for:
- Quality control and review
- Reprocessing if needed
- Debugging and validation
- Visualization in UI

### 3.4 Storage Format for ROI Features

```json
{
  "patient_id": "patient-002",
  "session_date": "2024-01-15",
  "preprocessing_version": "1.0",
  "preprocessing_timestamp": "2024-01-15T10:30:00Z",
  "mri_roi_features": [
    0.523, 0.612, 0.489, ..., 0.701  // 93 values
  ],
  "pet_roi_features": [
    1.234, 1.156, 1.089, ..., 1.312  // 93 values
  ],
  "quality_metrics": {
    "mri_snr": 25.3,
    "pet_mean_suvr": 1.15,
    "registration_quality": "good",
    "motion_artifacts": "none"
  },
  "atlas_registration": {
    "method": "SyN",
    "iterations": 100,
    "convergence": 0.0001
  }
}
```

---

## 4. STAGE 2: ONLINE PREDICTION (Real-Time)

### 4.1 When to Run

**Trigger**: User clicks "Predict Alzheimer's Progression" button

**Execution**: Synchronous API call

**Frequency**: On-demand (multiple times per patient)

### 4.2 Processing Steps

```python
# STAGE 2: Online Prediction Pipeline
# Triggered by: User request for prediction
# Execution: Real-time API endpoint
# Time: 30-60 seconds

@app.post("/api/v1/adni/predict-progression")
async def predict_progression(patient_id: str):
    """
    Fast prediction using pre-computed features.
    """
    start_time = time.time()
    
    # 1. Fetch patient demographics from FHIR (FAST)
    patient = await fhir_client.get(f"Patient/{patient_id}")  # ~100ms
    demographics = extract_demographics(patient)
    
    # 2. Fetch all imaging sessions for patient (FAST)
    imaging_studies = await fhir_client.search(
        "ImagingStudy",
        params={"patient": patient_id}
    )  # ~200ms
    
    # 3. Fetch pre-computed ROI features from cloud (FAST)
    all_features = []
    for study in imaging_studies:
        # Get preprocessed features URL from FHIR extension
        features_url = study["extension"]["preprocessed-features-url"]
        
        # Download pre-computed features (tiny file, ~2 KB)
        roi_features = await download_json(features_url)  # ~50ms per session
        
        all_features.append({
            "session_date": study["started"][:10],
            "mri_roi": roi_features["mri_roi_features"],  # 93 values
            "pet_roi": roi_features["pet_roi_features"],  # 93 values
        })
    
    # 4. Fetch cognitive scores from FHIR (FAST)
    observations = await fhir_client.search(
        "Observation",
        params={
            "patient": patient_id,
            "code": "72106-8,52493-4,54629-3"  # MMSE, CDR, ADAS
        }
    )  # ~200ms
    
    # 5. Assemble feature matrix (FAST)
    X, Y, masks = assemble_feature_matrix(
        demographics=demographics,
        roi_features=all_features,
        cognitive_scores=observations
    )  # ~100ms
    
    # 6. Load pre-trained model (FAST - cached in memory)
    model = load_model("best_seq_model_FIXED.pt")  # ~500ms (first time only)
    
    # 7. Run inference (FAST)
    predictions = model.predict(X, Y, masks)  # ~5-10s
    
    # 8. Format results
    results = {
        "patient_id": patient_id,
        "prediction_timestamp": datetime.now().isoformat(),
        "historical_visits": len(all_features),
        "predictions": {
            "6_months": {
                "mmse": predictions["mmse"][0],
                "cdr_global": predictions["cdr_global"][0],
                "cdr_sob": predictions["cdr_sob"][0],
                "adas_cog": predictions["adas_cog"][0]
            },
            "12_months": {
                "mmse": predictions["mmse"][1],
                "cdr_global": predictions["cdr_global"][1],
                "cdr_sob": predictions["cdr_sob"][1],
                "adas_cog": predictions["adas_cog"][1]
            },
            # ... up to 5 years
        },
        "confidence_scores": predictions["confidence"],
        "processing_time_seconds": time.time() - start_time
    }
    
    return results
```

### 4.3 Time Breakdown (Optimized)

| Stage | Task | Time |
|-------|------|------|
| 1 | Fetch patient demographics (FHIR) | ~100ms |
| 2 | Fetch imaging studies (FHIR) | ~200ms |
| 3 | Download ROI features (10 sessions × 2KB) | ~500ms |
| 4 | Fetch cognitive scores (FHIR) | ~200ms |
| 5 | Assemble feature matrix | ~100ms |
| 6 | Load model (cached) | ~50ms |
| 7 | Model inference | ~5-10s |
| 8 | Format results | ~50ms |

**Total**: **~7-12 seconds** (vs 15-20 minutes unoptimized)

**Speedup**: **~100x faster** 🚀

---

## 5. ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMAGING SCAN UPLOAD                          │
│                  (FHIR ImagingStudy POST)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 1: OFFLINE PREPROCESSING                     │
│                  (Background Worker)                            │
│                                                                 │
│  1. Download raw MRI/PET from cloud         [30s]              │
│  2. N4 bias correction                      [2-3min]           │
│  3. Brain extraction (SyN registration)     [3-5min]           │
│  4. PET → T1 registration                   [1-2min]           │
│  5. SUVR normalization                      [30s]              │
│  6. Atlas registration (SyN)                [5-10min]          │
│  7. ROI feature extraction                  [1min]             │
│                                                                 │
│  Total Time: ~15-20 minutes                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CLOUD STORAGE (S3/Azure)                       │
│                                                                 │
│  preprocessed/{patient_id}/{session_date}/                     │
│  ├── mri_brain.nii.gz                                          │
│  ├── pet_suvr.nii.gz                                           │
│  ├── atlas_in_t1.nii.gz                                        │
│  └── roi_features.json  ⭐ (2 KB - 186 features)               │
│                                                                 │
│  Update FHIR ImagingStudy with preprocessing status            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ (Hours/Days later)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 USER REQUESTS PREDICTION                        │
│              (Click "Predict Progression")                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              STAGE 2: ONLINE PREDICTION                         │
│                  (Real-Time API)                                │
│                                                                 │
│  1. Fetch demographics from FHIR            [100ms]            │
│  2. Fetch imaging studies from FHIR         [200ms]            │
│  3. Download ROI features (2KB × 10)        [500ms]            │
│  4. Fetch cognitive scores from FHIR        [200ms]            │
│  5. Assemble feature matrix                 [100ms]            │
│  6. Load model (cached)                     [50ms]             │
│  7. Model inference                         [5-10s]            │
│  8. Format results                          [50ms]             │
│                                                                 │
│  Total Time: ~7-12 seconds                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PREDICTION RESULTS                             │
│                                                                 │
│  - 6-month predictions (MMSE, CDR, ADAS)                       │
│  - 12-month predictions                                        │
│  - 18-month predictions                                        │
│  - ... up to 5 years                                           │
│  - Confidence scores                                           │
│  - Progression trajectory visualization                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. IMPLEMENTATION DETAILS

### 6.1 Background Worker Setup (Stage 1)

**Option A: Celery + Redis**
```python
# tasks.py
from celery import Celery

app = Celery('adni_preprocessing', broker='redis://localhost:6379')

@app.task(bind=True)
def preprocess_imaging_study(self, imaging_study_id):
    """
    Background task for preprocessing.
    """
    try:
        # Update task status
        self.update_state(state='PROCESSING', meta={'progress': 0})
        
        # Run preprocessing pipeline
        result = offline_preprocessing_pipeline(imaging_study_id)
        
        # Update task status
        self.update_state(state='SUCCESS', meta={'progress': 100})
        
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

# Trigger from FHIR upload
@app.post("/ImagingStudy")
async def create_imaging_study(imaging_study: dict):
    # Save to FHIR
    fhir_client.create("ImagingStudy", imaging_study)
    
    # Trigger background preprocessing
    task = preprocess_imaging_study.delay(imaging_study["id"])
    
    return {
        "id": imaging_study["id"],
        "preprocessing_task_id": task.id,
        "status": "preprocessing_queued"
    }
```

**Option B: AWS Lambda + SQS**
```python
# Lambda function triggered by S3 upload
def lambda_handler(event, context):
    # S3 upload event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Download image
    s3_client.download_file(bucket, key, '/tmp/image.nii.gz')
    
    # Run preprocessing
    result = offline_preprocessing_pipeline('/tmp/image.nii.gz')
    
    # Upload results
    s3_client.upload_file(result, bucket, f'preprocessed/{key}')
    
    return {'statusCode': 200}
```

### 6.2 Caching Strategy (Stage 2)

**Model Caching**:
```python
# Cache model in memory (singleton pattern)
class ModelCache:
    _instance = None
    _model = None
    
    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = torch.load("best_seq_model_FIXED.pt")
            cls._model.eval()
        return cls._model

# Use in API
model = ModelCache.get_model()  # Only loads once
```

**Feature Caching** (Optional):
```python
# Cache ROI features in Redis for frequently accessed patients
@cache(ttl=3600)  # Cache for 1 hour
async def get_roi_features(patient_id, session_date):
    features_url = get_features_url(patient_id, session_date)
    return await download_json(features_url)
```

---

## 7. STORAGE OPTIMIZATION

### 7.1 Storage Comparison

| Storage Strategy | Size per Session | 10 Sessions | 100 Patients |
|------------------|------------------|-------------|--------------|
| Raw DICOM | ~500 MB | ~5 GB | ~50 GB |
| Raw NIfTI | ~60 MB | ~600 MB | ~6 GB |
| Preprocessed Images | ~52 MB | ~520 MB | ~5.2 GB |
| **ROI Features Only** | **~2 KB** | **~20 KB** | **~200 KB** |

**Recommendation**: 
- Store **preprocessed images** (52 MB) for quality control
- Store **ROI features** (2 KB) for fast prediction
- Archive **raw DICOM** to cold storage (S3 Glacier)

### 7.2 Cost Analysis (AWS S3)

**Scenario**: 1000 patients, 5 sessions each

| Storage Type | Size | S3 Standard | S3 Glacier |
|--------------|------|-------------|------------|
| Raw DICOM | 2.5 TB | $57/month | $1/month |
| Preprocessed | 260 GB | $6/month | $0.26/month |
| ROI Features | 10 MB | $0.0002/month | - |

**Optimal Strategy**:
- **Hot Storage** (S3 Standard): ROI features (~$0.0002/month)
- **Warm Storage** (S3 Standard): Preprocessed images (~$6/month)
- **Cold Storage** (S3 Glacier): Raw DICOM (~$1/month)

---

## 8. QUALITY CONTROL & MONITORING

### 8.1 Preprocessing Quality Checks

```python
def compute_qc_metrics(mri_brain, pet_suvr):
    """
    Compute quality control metrics for preprocessed images.
    """
    return {
        "mri_snr": compute_snr(mri_brain),
        "mri_brain_volume_ml": compute_brain_volume(mri_brain),
        "pet_mean_suvr": np.mean(pet_suvr),
        "pet_std_suvr": np.std(pet_suvr),
        "registration_quality": assess_registration_quality(mri_brain),
        "motion_artifacts": detect_motion_artifacts(mri_brain),
        "preprocessing_warnings": []
    }
```

### 8.2 Monitoring Dashboard

Track preprocessing pipeline health:
- **Queue Length**: Number of scans waiting for preprocessing
- **Processing Time**: Average time per scan
- **Success Rate**: % of scans successfully preprocessed
- **Storage Usage**: Total storage consumed
- **Quality Metrics**: Distribution of SNR, registration quality

---

## 9. FAILURE HANDLING

### 9.1 Preprocessing Failures

**Common Failures**:
1. **Registration failure** (poor image quality)
2. **Out of memory** (large images)
3. **Network timeout** (cloud download)

**Retry Strategy**:
```python
@app.task(bind=True, max_retries=3, default_retry_delay=300)
def preprocess_imaging_study(self, imaging_study_id):
    try:
        return offline_preprocessing_pipeline(imaging_study_id)
    except RegistrationError as e:
        # Don't retry registration failures
        raise
    except (NetworkError, MemoryError) as e:
        # Retry transient errors
        raise self.retry(exc=e)
```

### 9.2 Fallback Strategy

If preprocessing fails:
1. **Manual Review**: Flag for radiologist review
2. **Alternative Method**: Try simpler registration (rigid instead of SyN)
3. **Skip Session**: Exclude from model input (model handles missing data)

---

## 10. PERFORMANCE BENCHMARKS

### 10.1 Time Comparison

| Scenario | Unoptimized | Optimized | Speedup |
|----------|-------------|-----------|---------|
| **Single Patient (1 visit)** | 15-20 min | 7-12 sec | **~100x** |
| **Single Patient (10 visits)** | 150-200 min | 10-15 sec | **~900x** |
| **Batch (100 patients)** | 25-33 hours | 15-25 min | **~100x** |

### 10.2 User Experience

**Unoptimized**:
```
User clicks "Predict" → Wait 15-20 minutes → Results
❌ Unacceptable for real-time clinical use
```

**Optimized**:
```
Scan uploaded → Background preprocessing (15-20 min, async)
                ↓
User clicks "Predict" → Wait 10 seconds → Results
✅ Acceptable for clinical use
```

---

## 11. IMPLEMENTATION ROADMAP

### Phase 1: Basic Optimization (Week 1-2)
- [ ] Implement offline preprocessing pipeline
- [ ] Set up cloud storage for preprocessed features
- [ ] Implement online prediction API
- [ ] Test with single patient

### Phase 2: Production Infrastructure (Week 3-4)
- [ ] Set up Celery/Redis for background jobs
- [ ] Implement retry logic and error handling
- [ ] Add quality control metrics
- [ ] Set up monitoring dashboard

### Phase 3: Optimization & Scaling (Week 5-6)
- [ ] Implement caching (Redis)
- [ ] Optimize storage costs (S3 lifecycle policies)
- [ ] Parallel processing for batch predictions
- [ ] Load testing and performance tuning

### Phase 4: Advanced Features (Week 7-8)
- [ ] Incremental updates (new scans)
- [ ] Automatic reprocessing on model updates
- [ ] Quality control dashboard
- [ ] Admin tools for managing preprocessing queue

---

## 12. SUMMARY: KEY DECISIONS

### ✅ DO THIS

1. **Pre-compute ROI features** during scan upload (Stage 1)
2. **Store preprocessed images** for quality control
3. **Cache model in memory** for fast inference
4. **Use background workers** (Celery/Lambda) for preprocessing
5. **Store features in cloud** (S3/Azure Blob)
6. **Implement retry logic** for transient failures

### ❌ DON'T DO THIS

1. **Don't preprocess on-demand** (too slow)
2. **Don't store only raw images** (requires reprocessing)
3. **Don't run preprocessing synchronously** (blocks user)
4. **Don't skip quality control** (garbage in, garbage out)
5. **Don't use local storage** (not scalable)

---

## 13. FINAL ARCHITECTURE

```
┌──────────────────────────────────────────────────────────────┐
│                    UPLOAD SCAN                               │
│                       ↓                                      │
│              [Background Worker]                             │
│                       ↓                                      │
│         Preprocess (15-20 min, async)                       │
│                       ↓                                      │
│    Store ROI Features (2 KB) in Cloud                       │
│                       ↓                                      │
│         Update FHIR with status                             │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│              USER REQUESTS PREDICTION                        │
│                       ↓                                      │
│    Fetch ROI Features from Cloud (500ms)                    │
│                       ↓                                      │
│    Fetch Demographics/Scores (500ms)                        │
│                       ↓                                      │
│         Model Inference (5-10s)                             │
│                       ↓                                      │
│            Return Results                                    │
│                                                              │
│         TOTAL TIME: ~7-12 seconds                           │
└──────────────────────────────────────────────────────────────┘
```

**Result**: **100x faster predictions** with minimal storage overhead! 🚀

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-21  
**Author**: Smart EHR System - ADNI Optimization Team
