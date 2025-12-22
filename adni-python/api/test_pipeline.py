"""
Test Script for ADNI Prediction Pipeline
=========================================

This script tests the complete pipeline:
1. Checks if input data exists
2. Runs preprocessing (or uses cache)
3. Runs prediction
4. Displays results

Usage:
    python api/test_pipeline.py --patient_id patient-002
"""

import sys
import subprocess
import json
from pathlib import Path
import argparse

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_DIR = SCRIPT_DIR / "input_data"
PREPROCESSED_DIR = SCRIPT_DIR / "preprocessed_data"
PREDICTIONS_DIR = SCRIPT_DIR / "predictions"


def check_input_data(patient_id):
    """Check if input data exists for patient."""
    print(f"\n{'='*80}")
    print(f"Checking Input Data for {patient_id}")
    print(f"{'='*80}\n")
    
    patient_dir = INPUT_DIR / patient_id
    clinical_file = patient_dir / "clinical_data.json"
    
    if not patient_dir.exists():
        print(f"✗ Patient directory not found: {patient_dir}")
        print(f"\nPlease create:")
        print(f"  {patient_dir}/")
        print(f"  ├── clinical_data.json")
        print(f"  └── {{session_date}}/")
        print(f"      ├── mri.nii.gz")
        print(f"      └── pet.nii.gz")
        return False
    
    if not clinical_file.exists():
        print(f"✗ Clinical data not found: {clinical_file}")
        print(f"\nSee api/input_data/EXAMPLE_clinical_data.json for format")
        return False
    
    # Load clinical data
    with open(clinical_file, 'r') as f:
        clinical_data = json.load(f)
    
    sessions = clinical_data.get("sessions", [])
    if len(sessions) == 0:
        print(f"✗ No sessions found in clinical_data.json")
        return False
    
    print(f"✓ Clinical data found: {len(sessions)} session(s)")
    
    # Check each session
    missing_sessions = []
    for session in sessions:
        session_date = session["session_date"]
        session_dir = patient_dir / session_date
        mri_file = session_dir / "mri.nii.gz"
        pet_file = session_dir / "pet.nii.gz"
        
        if not session_dir.exists():
            missing_sessions.append(session_date)
            print(f"✗ Session directory not found: {session_dir}")
        elif not mri_file.exists():
            missing_sessions.append(session_date)
            print(f"✗ MRI not found: {mri_file}")
        elif not pet_file.exists():
            missing_sessions.append(session_date)
            print(f"✗ PET not found: {pet_file}")
        else:
            print(f"✓ Session {session_date}: MRI and PET found")
    
    if missing_sessions:
        print(f"\n✗ Missing data for {len(missing_sessions)} session(s)")
        print(f"\nPlease add MRI and PET files for:")
        for date in missing_sessions:
            print(f"  - {patient_dir}/{date}/mri.nii.gz")
            print(f"  - {patient_dir}/{date}/pet.nii.gz")
        return False
    
    print(f"\n✓ All input data present\n")
    return True


def run_preprocessing(patient_id, force=False):
    """Run preprocessing for all sessions."""
    print(f"\n{'='*80}")
    print(f"Preprocessing")
    print(f"{'='*80}\n")
    
    # Load clinical data to get sessions
    clinical_file = INPUT_DIR / patient_id / "clinical_data.json"
    with open(clinical_file, 'r') as f:
        clinical_data = json.load(f)
    
    sessions = clinical_data.get("sessions", [])
    
    for i, session in enumerate(sessions, 1):
        session_date = session["session_date"]
        
        print(f"[{i}/{len(sessions)}] Preprocessing session: {session_date}")
        
        # Check if already preprocessed
        roi_features_path = PREPROCESSED_DIR / patient_id / session_date / "roi_features.json"
        
        if roi_features_path.exists() and not force:
            print(f"  ✓ Already preprocessed (using cache)")
            continue
        
        # Run preprocessing
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "preprocess_patient.py"),
            "--patient_id", patient_id,
            "--session_date", session_date
        ]
        
        if force:
            cmd.append("--force")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  ✗ Preprocessing failed:")
            print(result.stderr)
            return False
        
        print(f"  ✓ Preprocessing completed")
    
    print(f"\n✓ All sessions preprocessed\n")
    return True


def run_prediction(patient_id):
    """Run prediction."""
    print(f"\n{'='*80}")
    print(f"Running Prediction")
    print(f"{'='*80}\n")
    
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "predict_progression.py"),
        "--patient_id", patient_id
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"✗ Prediction failed:")
        print(result.stderr)
        return False
    
    # Print output
    print(result.stdout)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Test ADNI prediction pipeline")
    parser.add_argument("--patient_id", required=True, help="Patient ID (e.g., patient-002)")
    parser.add_argument("--force", action="store_true", help="Force reprocessing")
    parser.add_argument("--skip-preprocess", action="store_true", help="Skip preprocessing (use cached)")
    
    args = parser.parse_args()
    
    print(f"\n{'#'*80}")
    print(f"# ADNI Prediction Pipeline Test")
    print(f"# Patient ID: {args.patient_id}")
    print(f"{'#'*80}")
    
    # Step 1: Check input data
    if not check_input_data(args.patient_id):
        print(f"\n✗ Input data check failed. Please add required files.\n")
        sys.exit(1)
    
    # Step 2: Run preprocessing
    if not args.skip_preprocess:
        if not run_preprocessing(args.patient_id, args.force):
            print(f"\n✗ Preprocessing failed.\n")
            sys.exit(1)
    else:
        print(f"\n⚠ Skipping preprocessing (using cached data)\n")
    
    # Step 3: Run prediction
    if not run_prediction(args.patient_id):
        print(f"\n✗ Prediction failed.\n")
        sys.exit(1)
    
    print(f"\n{'#'*80}")
    print(f"# ✓ Pipeline test completed successfully!")
    print(f"{'#'*80}\n")
    
    sys.exit(0)


if __name__ == "__main__":
    main()
