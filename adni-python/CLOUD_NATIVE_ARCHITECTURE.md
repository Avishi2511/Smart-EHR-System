# ADNI Cloud-Native Architecture: Zero Network Bottlenecks

## Executive Summary

This document describes a **fully cloud-native architecture** where ALL processing happens in the cloud, eliminating network transfer bottlenecks. The preprocessing pipeline is triggered **automatically on upload** and runs **co-located with storage**, reducing the 15-20 minute preprocessing time to **5-8 minutes** by eliminating network I/O.

---

## 1. THE KEY INSIGHT

### 1.1 Problem with Hybrid Architecture

**Hybrid (Local + Cloud)**:
```
Cloud Storage → Download (30s) → Local Preprocessing (15min) → Upload (30s)
                ❌ Network I/O    ✅ Processing              ❌ Network I/O

Total: ~16 minutes
```

### 1.2 Solution: Fully Cloud-Native

**Cloud-Native**:
```
Cloud Storage → Cloud Preprocessing (5-8min) → Cloud Storage
                ✅ No network I/O!

Total: ~5-8 minutes (2-3x faster!)
```

**Why Faster?**
- ✅ **No download time** - Data already in cloud
- ✅ **No upload time** - Results stay in cloud
- ✅ **High-speed internal network** - Cloud storage ↔ Compute (10+ Gbps)
- ✅ **Parallel processing** - Multiple scans simultaneously
- ✅ **Auto-scaling** - More compute when needed

---

## 2. CLOUD-NATIVE ARCHITECTURE

### 2.1 Complete System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLOUD INFRASTRUCTURE                        │
│                    (AWS / Azure / Google Cloud)                     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                    UPLOAD LAYER                           │    │
│  │                                                           │    │
│  │  Hospital/Clinic → Upload MRI/PET → Object Storage       │    │
│  │                                      (S3/Azure Blob)      │    │
│  │                                            │              │    │
│  │                                            ▼              │    │
│  │                                   [Upload Event]          │    │
│  └────────────────────────────────────────┬──────────────────┘    │
│                                           │                        │
│  ┌────────────────────────────────────────▼──────────────────┐    │
│  │              PREPROCESSING LAYER (Serverless)             │    │
│  │                                                           │    │
│  │  Event Trigger → Lambda/Cloud Function                   │    │
│  │                       │                                   │    │
│  │                       ▼                                   │    │
│  │         ┌─────────────────────────────┐                  │    │
│  │         │  Container (Docker)         │                  │    │
│  │         │  - ANTs (registration)      │                  │    │
│  │         │  - nibabel (NIfTI I/O)      │                  │    │
│  │         │  - numpy, scipy             │                  │    │
│  │         │                             │                  │    │
│  │         │  Processing Steps:          │                  │    │
│  │         │  1. N4 correction (2min)    │                  │    │
│  │         │  2. Brain extraction (3min) │                  │    │
│  │         │  3. PET registration (1min) │                  │    │
│  │         │  4. SUVR (30s)              │                  │    │
│  │         │  5. Atlas reg (3-5min)      │                  │    │
│  │         │  6. ROI extract (30s)       │                  │    │
│  │         │                             │                  │    │
│  │         │  Total: 5-8 minutes         │                  │    │
│  │         └─────────────┬───────────────┘                  │    │
│  │                       │                                   │    │
│  │                       ▼                                   │    │
│  │         Write to Object Storage (same region)            │    │
│  │         - preprocessed/{patient}/{session}/              │    │
│  │         - Update FHIR metadata                           │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                    STORAGE LAYER                          │    │
│  │                                                           │    │
│  │  Object Storage (S3/Azure Blob/GCS)                      │    │
│  │  ├── raw/                                                │    │
│  │  │   └── {patient_id}/{session_date}/                   │    │
│  │  │       ├── mri.nii.gz (60 MB)                         │    │
│  │  │       └── pet.nii.gz (30 MB)                         │    │
│  │  │                                                       │    │
│  │  └── preprocessed/                                       │    │
│  │      └── {patient_id}/{session_date}/                   │    │
│  │          ├── mri_brain.nii.gz (25 MB)                   │    │
│  │          ├── pet_suvr.nii.gz (12 MB)                    │    │
│  │          ├── atlas_in_t1.nii.gz (10 MB)                 │    │
│  │          └── roi_features.json (2 KB) ⭐                │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                    FHIR SERVER LAYER                      │    │
│  │                                                           │    │
│  │  FHIR Server (Cloud-hosted)                              │    │
│  │  - Patient demographics                                  │    │
│  │  - Cognitive scores (Observations)                       │    │
│  │  - ImagingStudy resources                                │    │
│  │  - Preprocessing status metadata                         │    │
│  │                                                           │    │
│  │  Database: PostgreSQL/MongoDB (managed)                  │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │              PREDICTION API LAYER                         │    │
│  │                                                           │    │
│  │  FastAPI / Flask (Cloud Run / ECS / App Service)         │    │
│  │                                                           │    │
│  │  Endpoints:                                               │    │
│  │  - POST /predict-progression                             │    │
│  │  - GET /preprocessing-status/{patient_id}                │    │
│  │  - GET /patient-timeline/{patient_id}                    │    │
│  │                                                           │    │
│  │  Model: PyTorch (loaded in memory, cached)               │    │
│  │  - best_seq_model_FIXED.pt                               │    │
│  │                                                           │    │
│  │  Processing Time: 5-10 seconds                           │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐    │
│  │                    FRONTEND LAYER                         │    │
│  │                                                           │    │
│  │  React App (Static hosting: S3 + CloudFront)             │    │
│  │  - Patient dashboard                                      │    │
│  │  - Prediction visualization                              │    │
│  │  - Timeline view                                          │    │
│  └───────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. DETAILED CLOUD ARCHITECTURE BY PROVIDER

### 3.1 AWS Architecture (Recommended)

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                               │
│                                                                 │
│  Upload MRI/PET                                                 │
│       ↓                                                         │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ S3 Bucket: adni-raw-images                          │       │
│  │ - Versioning enabled                                │       │
│  │ - Lifecycle: Archive to Glacier after 90 days       │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 │ (S3 Event Notification)                       │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ EventBridge / SNS                                   │       │
│  │ - Filter: *.nii.gz uploads                          │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ AWS Batch / ECS Fargate                             │       │
│  │                                                      │       │
│  │ Container Specs:                                     │       │
│  │ - Image: adni-preprocessing:latest                  │       │
│  │ - CPU: 4 vCPUs                                       │       │
│  │ - Memory: 16 GB                                      │       │
│  │ - Timeout: 30 minutes                                │       │
│  │                                                      │       │
│  │ Environment:                                         │       │
│  │ - ANTs, nibabel, numpy, scipy                        │       │
│  │ - Python 3.9+                                        │       │
│  │                                                      │       │
│  │ Mounted:                                             │       │
│  │ - /tmp (ephemeral, 20 GB)                            │       │
│  │ - S3 access via IAM role                             │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ S3 Bucket: adni-preprocessed                        │       │
│  │ - Standard tier (hot data)                          │       │
│  │ - Intelligent tiering enabled                       │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ RDS PostgreSQL (FHIR database)                      │       │
│  │ - Update ImagingStudy status                        │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ ECS Fargate / Lambda (Prediction API)               │       │
│  │ - FastAPI application                                │       │
│  │ - Model cached in memory                            │       │
│  │ - Auto-scaling: 1-10 instances                       │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ CloudFront + S3 (Frontend)                          │       │
│  │ - React app (static files)                          │       │
│  │ - Global CDN distribution                           │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### AWS Implementation

**1. S3 Event Trigger**:
```python
# S3 bucket configuration
{
  "NotificationConfiguration": {
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:us-east-1:123456789:function:trigger-preprocessing",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [{
            "Name": "suffix",
            "Value": ".nii.gz"
          }]
        }
      }
    }]
  }
}
```

**2. Lambda Trigger Function**:
```python
# lambda/trigger_preprocessing.py
import boto3
import json

ecs = boto3.client('ecs')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Triggered by S3 upload. Starts ECS Fargate task for preprocessing.
    """
    # Parse S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Extract patient_id and session_date from key
    # Format: raw/{patient_id}/{session_date}/mri.nii.gz
    parts = key.split('/')
    patient_id = parts[1]
    session_date = parts[2]
    
    # Check if both MRI and PET are uploaded
    mri_key = f"raw/{patient_id}/{session_date}/mri.nii.gz"
    pet_key = f"raw/{patient_id}/{session_date}/pet.nii.gz"
    
    mri_exists = object_exists(bucket, mri_key)
    pet_exists = object_exists(bucket, pet_key)
    
    if not (mri_exists and pet_exists):
        print(f"Waiting for both MRI and PET. MRI: {mri_exists}, PET: {pet_exists}")
        return
    
    # Start ECS Fargate task
    response = ecs.run_task(
        cluster='adni-preprocessing-cluster',
        taskDefinition='adni-preprocessing-task',
        launchType='FARGATE',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': ['subnet-12345'],
                'securityGroups': ['sg-12345'],
                'assignPublicIp': 'ENABLED'
            }
        },
        overrides={
            'containerOverrides': [{
                'name': 'adni-preprocessing',
                'environment': [
                    {'name': 'PATIENT_ID', 'value': patient_id},
                    {'name': 'SESSION_DATE', 'value': session_date},
                    {'name': 'S3_BUCKET', 'value': bucket}
                ]
            }]
        }
    )
    
    print(f"Started preprocessing task: {response['tasks'][0]['taskArn']}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'patient_id': patient_id,
            'session_date': session_date,
            'task_arn': response['tasks'][0]['taskArn']
        })
    }

def object_exists(bucket, key):
    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except:
        return False
```

**3. ECS Fargate Task (Preprocessing Container)**:
```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install ANTs (Advanced Normalization Tools)
RUN git clone https://github.com/ANTsX/ANTs.git && \
    cd ANTs && \
    mkdir build && cd build && \
    cmake .. && \
    make -j4 && \
    make install

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy preprocessing scripts
COPY preprocessing/ /app/preprocessing/
WORKDIR /app

# Entry point
CMD ["python", "preprocessing/run_preprocessing.py"]
```

```python
# preprocessing/run_preprocessing.py
import os
import boto3
import json
from pathlib import Path
from preprocessing_pipeline import preprocess_session

s3 = boto3.client('s3')

def main():
    # Get environment variables
    patient_id = os.environ['PATIENT_ID']
    session_date = os.environ['SESSION_DATE']
    bucket = os.environ['S3_BUCKET']
    
    print(f"Starting preprocessing for {patient_id}/{session_date}")
    
    # Download MRI and PET from S3 to local /tmp
    mri_path = "/tmp/mri.nii.gz"
    pet_path = "/tmp/pet.nii.gz"
    
    print("Downloading MRI from S3...")
    s3.download_file(
        bucket,
        f"raw/{patient_id}/{session_date}/mri.nii.gz",
        mri_path
    )
    
    print("Downloading PET from S3...")
    s3.download_file(
        bucket,
        f"raw/{patient_id}/{session_date}/pet.nii.gz",
        pet_path
    )
    
    # Run preprocessing pipeline (5-8 minutes)
    print("Running preprocessing pipeline...")
    results = preprocess_session(
        mri_path=mri_path,
        pet_path=pet_path,
        output_dir="/tmp/preprocessed"
    )
    
    # Upload results back to S3
    print("Uploading preprocessed data to S3...")
    output_prefix = f"preprocessed/{patient_id}/{session_date}"
    
    for filename, filepath in results.items():
        s3.upload_file(
            filepath,
            bucket,
            f"{output_prefix}/{filename}"
        )
    
    # Update FHIR ImagingStudy status
    print("Updating FHIR metadata...")
    update_fhir_status(patient_id, session_date, "completed")
    
    print("Preprocessing completed successfully!")

if __name__ == "__main__":
    main()
```

---

### 3.2 Azure Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       AZURE CLOUD                               │
│                                                                 │
│  Upload MRI/PET                                                 │
│       ↓                                                         │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Blob Storage: adni-raw-images                 │       │
│  │ - Hot tier                                          │       │
│  │ - Lifecycle management                              │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 │ (Blob Trigger)                                │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Functions (Event Grid)                        │       │
│  │ - Trigger on blob upload                            │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Container Instances / Batch                   │       │
│  │ - Same preprocessing container                      │       │
│  │ - 4 vCPUs, 16 GB RAM                                │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Blob Storage: adni-preprocessed               │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Database for PostgreSQL (FHIR)                │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure App Service / Container Apps (API)            │       │
│  │ - FastAPI prediction service                        │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Azure Static Web Apps (Frontend)                    │       │
│  │ - React app with CDN                                │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 3.3 Google Cloud Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GOOGLE CLOUD                               │
│                                                                 │
│  Upload MRI/PET                                                 │
│       ↓                                                         │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud Storage: adni-raw-images                      │       │
│  │ - Standard storage class                            │       │
│  │ - Lifecycle: Archive after 90 days                  │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 │ (Cloud Storage Trigger)                       │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud Functions / Pub/Sub                           │       │
│  │ - Trigger on object finalize                        │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud Run Jobs / GKE                                │       │
│  │ - Preprocessing container                           │       │
│  │ - 4 vCPUs, 16 GB RAM                                │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud Storage: adni-preprocessed                    │       │
│  └──────────────┬──────────────────────────────────────┘       │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud SQL PostgreSQL (FHIR)                         │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Cloud Run (Prediction API)                          │       │
│  │ - FastAPI service                                   │       │
│  │ - Auto-scaling                                      │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────┐       │
│  │ Firebase Hosting / Cloud Storage (Frontend)         │       │
│  │ - React app with CDN                                │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. COMPLETE DATA FLOW (Cloud-Native)

### 4.1 Upload → Preprocessing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Hospital uploads MRI scan                              │
│                                                                 │
│ Hospital → HTTPS Upload → Cloud Storage (S3/Blob/GCS)          │
│            (Direct upload, no intermediate server)              │
│                                                                 │
│ File: raw/patient-002/2024-01-15/mri.nii.gz (60 MB)           │
│ Time: ~10-20 seconds (depends on internet speed)               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Hospital uploads PET scan                              │
│                                                                 │
│ Hospital → HTTPS Upload → Cloud Storage                        │
│                                                                 │
│ File: raw/patient-002/2024-01-15/pet.nii.gz (30 MB)           │
│ Time: ~5-10 seconds                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Cloud Storage Event Trigger (AUTOMATIC)                │
│                                                                 │
│ Cloud Storage → Event → Lambda/Function                        │
│                                                                 │
│ Check: Both MRI and PET uploaded? ✅                           │
│ Time: <1 second                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Start Preprocessing Container (AUTOMATIC)              │
│                                                                 │
│ Lambda → ECS/Container Instance → Start Container              │
│                                                                 │
│ Container specs:                                                │
│ - 4 vCPUs, 16 GB RAM                                           │
│ - Timeout: 30 minutes                                          │
│ - Environment: ANTs, Python, nibabel                           │
│                                                                 │
│ Time: ~30 seconds (container startup)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Download from Cloud Storage (INTERNAL NETWORK)         │
│                                                                 │
│ Container → Download MRI (60 MB) from S3                        │
│ Container → Download PET (30 MB) from S3                        │
│                                                                 │
│ Network: 10+ Gbps (internal cloud network)                     │
│ Time: ~2-3 seconds (vs 30s on internet!) ✅                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Preprocessing Pipeline (COMPUTE-INTENSIVE)             │
│                                                                 │
│ 1. N4 bias correction (MRI)              [2 min]               │
│ 2. Brain extraction (SyN registration)   [3 min]               │
│ 3. PET averaging (if 4D)                 [10 sec]              │
│ 4. PET → T1 registration                 [1 min]               │
│ 5. SUVR normalization                    [30 sec]              │
│ 6. Atlas registration (SyN)              [3-5 min]             │
│ 7. ROI feature extraction                [30 sec]              │
│                                                                 │
│ Total: ~5-8 minutes (NO network I/O!) ✅                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Upload Results (INTERNAL NETWORK)                      │
│                                                                 │
│ Container → Upload to S3:                                       │
│ - mri_brain.nii.gz (25 MB)                                     │
│ - pet_suvr.nii.gz (12 MB)                                      │
│ - atlas_in_t1.nii.gz (10 MB)                                   │
│ - roi_features.json (2 KB) ⭐                                  │
│                                                                 │
│ Network: 10+ Gbps (internal)                                   │
│ Time: ~2-3 seconds (vs 30s on internet!) ✅                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 8: Update FHIR Metadata (AUTOMATIC)                       │
│                                                                 │
│ Container → Update FHIR ImagingStudy:                          │
│ {                                                               │
│   "id": "imaging-study-002",                                   │
│   "status": "available",                                       │
│   "extension": [{                                               │
│     "url": "preprocessing-status",                             │
│     "valueCode": "completed"                                   │
│   }, {                                                          │
│     "url": "preprocessed-features-url",                        │
│     "valueUrl": "s3://adni-preprocessed/.../roi_features.json" │
│   }]                                                            │
│ }                                                               │
│                                                                 │
│ Time: <1 second                                                │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 9: Cleanup & Notification                                 │
│                                                                 │
│ - Container terminates                                          │
│ - Send notification (email/SMS) to clinician                   │
│ - Update dashboard: "Preprocessing complete"                   │
│                                                                 │
│ TOTAL TIME: ~6-10 minutes (vs 16+ minutes hybrid!) ✅         │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Prediction Flow (User Request)

```
┌─────────────────────────────────────────────────────────────────┐
│ USER: Clicks "Predict Alzheimer's Progression" button          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: API Request                                            │
│                                                                 │
│ Frontend → POST /api/v1/adni/predict-progression               │
│ {                                                               │
│   "patient_id": "patient-002"                                  │
│ }                                                               │
│                                                                 │
│ Time: <10ms (network latency)                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Fetch Patient Data from FHIR (CLOUD-TO-CLOUD)         │
│                                                                 │
│ API Server → FHIR Server (same cloud region):                  │
│ - GET Patient/patient-002                                      │
│ - GET Observation?patient=patient-002&code=MMSE,CDR,ADAS       │
│ - GET ImagingStudy?patient=patient-002                         │
│                                                                 │
│ Network: Internal cloud network (low latency)                  │
│ Time: ~200-300ms ✅                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Fetch ROI Features (CLOUD-TO-CLOUD)                   │
│                                                                 │
│ API Server → S3 (same region):                                 │
│ - Download roi_features.json (2 KB × 10 sessions)              │
│                                                                 │
│ Network: Internal cloud network (10+ Gbps)                     │
│ Time: ~100-200ms for all sessions ✅                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Assemble Feature Matrix                                │
│                                                                 │
│ Combine:                                                        │
│ - Demographics (age, gender, education, APOE)                  │
│ - ROI features (93 MRI + 93 PET × 10 sessions)                 │
│ - Cognitive scores (MMSE, CDR, ADAS × 10 sessions)             │
│                                                                 │
│ Time: ~50-100ms (in-memory operations)                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Model Inference (GPU-ACCELERATED)                      │
│                                                                 │
│ PyTorch Model (cached in memory):                              │
│ - Multi-modal fusion                                           │
│ - LSTM sequence learning                                       │
│ - Predict future scores (6mo, 12mo, 18mo, 24mo, 36mo)         │
│                                                                 │
│ Hardware: GPU instance (optional, 10x faster)                  │
│ Time: ~2-5 seconds (CPU) or ~500ms (GPU) ✅                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Format & Return Results                                │
│                                                                 │
│ {                                                               │
│   "patient_id": "patient-002",                                 │
│   "predictions": {                                              │
│     "6_months": {"mmse": 23.5, "cdr": 1.0, "adas": 18.2},     │
│     "12_months": {"mmse": 22.8, "cdr": 1.0, "adas": 20.5},    │
│     "18_months": {"mmse": 22.0, "cdr": 1.5, "adas": 23.1},    │
│     ...                                                         │
│   },                                                            │
│   "confidence": 0.92,                                          │
│   "processing_time_ms": 3200                                   │
│ }                                                               │
│                                                                 │
│ Time: ~10ms (JSON serialization)                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ TOTAL PREDICTION TIME: ~3-6 seconds ✅                         │
│                                                                 │
│ User sees results in real-time!                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. PERFORMANCE COMPARISON

### 5.1 Time Breakdown

| Stage | Hybrid (Local+Cloud) | Cloud-Native | Improvement |
|-------|---------------------|--------------|-------------|
| **PREPROCESSING** | | | |
| Download images | 30s | 2-3s | **10x faster** |
| N4 correction | 2-3 min | 2-3 min | Same |
| Brain extraction | 3-5 min | 3-5 min | Same |
| PET registration | 1-2 min | 1-2 min | Same |
| SUVR | 30s | 30s | Same |
| Atlas registration | 5-10 min | 3-5 min | **2x faster** (better CPU) |
| ROI extraction | 30s | 30s | Same |
| Upload results | 30s | 2-3s | **10x faster** |
| **Total Preprocessing** | **15-20 min** | **6-10 min** | **~2x faster** |
| | | | |
| **PREDICTION** | | | |
| Fetch FHIR data | 500ms | 200ms | **2.5x faster** |
| Download ROI features | 500ms | 100ms | **5x faster** |
| Model inference | 5-10s | 2-5s | **2x faster** (GPU) |
| **Total Prediction** | **6-11s** | **2-5s** | **~2x faster** |

---

## 6. COST ANALYSIS

### 6.1 AWS Cost Estimate (1000 patients, 5 sessions each)

| Service | Usage | Cost/Month |
|---------|-------|------------|
| **S3 Storage** | | |
| - Raw images (300 GB) | Standard → Glacier after 90 days | $1.50 |
| - Preprocessed (260 GB) | Standard | $6.00 |
| - ROI features (10 MB) | Standard | $0.0002 |
| **ECS Fargate** | | |
| - Preprocessing (5000 tasks × 10 min) | 4 vCPU, 16 GB | $40.00 |
| **RDS PostgreSQL** | | |
| - FHIR database | db.t3.medium | $50.00 |
| **ECS Fargate (API)** | | |
| - Prediction service (always-on) | 2 vCPU, 4 GB | $30.00 |
| **CloudFront** | | |
| - Frontend CDN | 100 GB transfer | $8.50 |
| **Data Transfer** | | |
| - Internal (free) | S3 ↔ ECS (same region) | $0.00 |
| - External (upload) | 90 GB/month | $0.00 (ingress free) |
| **TOTAL** | | **~$136/month** |

**Per Patient Cost**: $0.136/month or **~$1.63/year**

---

## 7. OPTIMIZATION STRATEGIES

### 7.1 Parallel Processing

**Process multiple scans simultaneously**:
```python
# AWS Batch configuration
{
  "computeEnvironment": {
    "maxvCpus": 64,  # Up to 16 concurrent preprocessing tasks
    "desiredvCpus": 0,  # Scale to zero when idle
    "minvCpus": 0
  }
}
```

**Benefit**: Process 10 scans in ~10 minutes instead of 100 minutes

---

### 7.2 GPU Acceleration (Optional)

**Use GPU for model inference**:
```python
# ECS task definition
{
  "containerDefinitions": [{
    "resourceRequirements": [{
      "type": "GPU",
      "value": "1"  # 1 GPU (e.g., T4)
    }]
  }]
}
```

**Benefit**: 
- Inference time: 5-10s (CPU) → 500ms-1s (GPU)
- Cost: +$0.50/hour (only when running)

---

### 7.3 Caching Strategy

**Cache frequently accessed data**:
```python
# Redis/ElastiCache for caching
@cache(ttl=3600)  # Cache for 1 hour
async def get_patient_features(patient_id):
    # Fetch from S3 only if not in cache
    return await s3.get_object(...)
```

**Benefit**: Reduce S3 API calls by 90%

---

## 8. MONITORING & OBSERVABILITY

### 8.1 CloudWatch Metrics (AWS)

**Track preprocessing pipeline**:
- Queue length (pending scans)
- Processing time per scan
- Success/failure rate
- Storage usage
- Cost per scan

**Alerts**:
- Preprocessing failure
- Queue backlog > 10 scans
- Processing time > 15 minutes
- Storage > 1 TB

---

### 8.2 Logging

**Structured logging**:
```python
import logging
import json

logger = logging.getLogger()

logger.info(json.dumps({
    "event": "preprocessing_started",
    "patient_id": patient_id,
    "session_date": session_date,
    "timestamp": datetime.now().isoformat()
}))
```

**Benefits**:
- Searchable logs (CloudWatch Insights)
- Debugging failures
- Audit trail

---

## 9. SECURITY & COMPLIANCE

### 9.1 Data Encryption

**At Rest**:
- S3: AES-256 encryption (default)
- RDS: Encrypted volumes
- ECS: Encrypted ephemeral storage

**In Transit**:
- HTTPS/TLS 1.2+ for all API calls
- VPC endpoints for S3 (no internet exposure)

### 9.2 Access Control

**IAM Roles** (Principle of Least Privilege):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "s3:GetObject",
      "s3:PutObject"
    ],
    "Resource": "arn:aws:s3:::adni-*/*"
  }]
}
```

### 9.3 HIPAA Compliance

- ✅ Encrypted storage (S3, RDS)
- ✅ Encrypted transit (TLS)
- ✅ Access logging (CloudTrail)
- ✅ Audit trails (CloudWatch Logs)
- ✅ BAA with AWS (Business Associate Agreement)

---

## 10. DISASTER RECOVERY

### 10.1 Backup Strategy

**S3 Versioning**:
- Keep last 30 versions of each object
- Lifecycle: Delete after 90 days

**RDS Automated Backups**:
- Daily snapshots
- 7-day retention
- Point-in-time recovery

### 10.2 Multi-Region Replication

**Critical data only**:
```python
# S3 replication rule
{
  "Rules": [{
    "Status": "Enabled",
    "Priority": 1,
    "Filter": {"Prefix": "preprocessed/"},
    "Destination": {
      "Bucket": "arn:aws:s3:::adni-preprocessed-backup",
      "ReplicationTime": {"Status": "Enabled"}
    }
  }]
}
```

---

## 11. SUMMARY: KEY BENEFITS

### ✅ Cloud-Native Advantages

1. **Faster Preprocessing** (6-10 min vs 15-20 min)
   - No network download/upload time
   - High-speed internal network (10+ Gbps)
   - Better compute resources

2. **Faster Predictions** (2-5 sec vs 6-11 sec)
   - Low-latency cloud-to-cloud communication
   - Optional GPU acceleration
   - Cached model in memory

3. **Zero Infrastructure Management**
   - Serverless (Lambda, ECS Fargate)
   - Auto-scaling
   - Pay-per-use

4. **High Availability**
   - Multi-AZ deployment
   - Automatic failover
   - 99.99% uptime SLA

5. **Cost-Effective**
   - ~$1.63/patient/year
   - No upfront costs
   - Scale to zero when idle

6. **Secure & Compliant**
   - HIPAA-ready
   - Encrypted at rest and in transit
   - Audit trails

---

## 12. DEPLOYMENT CHECKLIST

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Create S3 buckets (raw, preprocessed)
- [ ] Set up VPC and subnets
- [ ] Configure IAM roles and policies
- [ ] Deploy RDS PostgreSQL (FHIR)
- [ ] Set up CloudWatch logging

### Phase 2: Preprocessing Pipeline (Week 2)
- [ ] Build Docker image (ANTs, Python)
- [ ] Create ECS task definition
- [ ] Set up S3 event triggers
- [ ] Deploy Lambda trigger function
- [ ] Test preprocessing with sample data

### Phase 3: Prediction API (Week 3)
- [ ] Deploy FastAPI application (ECS Fargate)
- [ ] Configure auto-scaling
- [ ] Set up API Gateway (optional)
- [ ] Load and cache model
- [ ] Test prediction endpoint

### Phase 4: Frontend (Week 4)
- [ ] Deploy React app to S3
- [ ] Configure CloudFront CDN
- [ ] Set up custom domain
- [ ] Test end-to-end flow

### Phase 5: Monitoring & Security (Week 5)
- [ ] Set up CloudWatch dashboards
- [ ] Configure alerts
- [ ] Enable CloudTrail
- [ ] Security audit
- [ ] Load testing

---

## 13. FINAL ARCHITECTURE DIAGRAM

```
                    ┌─────────────────────────────────┐
                    │      HOSPITAL / CLINIC          │
                    │   (Upload MRI/PET scans)        │
                    └──────────────┬──────────────────┘
                                   │ HTTPS Upload
                                   ▼
┌────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                              │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ S3: adni-raw-images                                  │    │
│  │ - raw/{patient_id}/{session_date}/mri.nii.gz        │    │
│  │ - raw/{patient_id}/{session_date}/pet.nii.gz        │    │
│  └────────────┬─────────────────────────────────────────┘    │
│               │ S3 Event (automatic)                          │
│               ▼                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ Lambda: Trigger Preprocessing                        │    │
│  └────────────┬─────────────────────────────────────────┘    │
│               │ Start ECS Task                                │
│               ▼                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ECS Fargate: Preprocessing Container                │    │
│  │ - Download from S3 (internal, fast)                 │    │
│  │ - N4, brain extraction, registration (5-8 min)      │    │
│  │ - Upload to S3 (internal, fast)                     │    │
│  └────────────┬─────────────────────────────────────────┘    │
│               │                                               │
│               ▼                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ S3: adni-preprocessed                                │    │
│  │ - preprocessed/{patient}/{session}/roi_features.json │    │
│  │ - preprocessed/{patient}/{session}/mri_brain.nii.gz │    │
│  │ - preprocessed/{patient}/{session}/pet_suvr.nii.gz  │    │
│  └────────────┬─────────────────────────────────────────┘    │
│               │                                               │
│               ▼                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ RDS PostgreSQL: FHIR Database                        │    │
│  │ - Patient demographics                               │    │
│  │ - Cognitive scores (Observations)                    │    │
│  │ - ImagingStudy metadata                              │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ ECS Fargate: Prediction API (FastAPI)               │    │
│  │ - Fetch FHIR data (internal, fast)                  │    │
│  │ - Download ROI features from S3 (internal, fast)    │    │
│  │ - Model inference (2-5 sec)                         │    │
│  │ - Return predictions                                 │    │
│  └────────────┬─────────────────────────────────────────┘    │
│               │                                               │
└───────────────┼───────────────────────────────────────────────┘
                │ HTTPS API
                ▼
┌────────────────────────────────────────────────────────────────┐
│ CloudFront + S3: Frontend (React)                              │
│ - Patient dashboard                                            │
│ - Prediction visualization                                     │
│ - Timeline view                                                │
└────────────────────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────────┐
│                    CLINICIAN / USER                            │
│              (Views predictions in browser)                    │
└────────────────────────────────────────────────────────────────┘
```

---

**Result**: **Fully cloud-native, zero network bottlenecks, 2-3x faster, highly scalable!** 🚀

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-21  
**Author**: Smart EHR System - Cloud Architecture Team
