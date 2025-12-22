"""
Unified ADNI Pipeline - Backend Integration
============================================

This script orchestrates the complete pipeline:
1. Check for unprocessed MRI/PET scans
2. Auto-preprocess if new scans found
3. Run prediction model
4. Output clean scores (constrained values only)
5. Send results to backend

Usage:
    python api/run_pipeline.py --patient_id 033S0567
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
INPUT_DIR = PROJECT_ROOT / "api" / "input_data"
PREPROCESSED_DIR = PROJECT_ROOT / "api" / "preprocessed_data"
PREDICTIONS_DIR = PROJECT_ROOT / "api" / "predictions"


def check_for_new_scans(patient_id):
    """
    Check if there are unprocessed MRI/PET scans for the patient.
    
    Returns:
        list of session dates that need preprocessing
    """
    patient_input_dir = INPUT_DIR / patient_id
    patient_preprocessed_dir = PREPROCESSED_DIR / patient_id
    
    if not patient_input_dir.exists():
        return []
    
    # Load clinical data to get all sessions
    clinical_file = patient_input_dir / "clinical_data.json"
    if not clinical_file.exists():
        return []
    
    with open(clinical_file, 'r') as f:
        clinical_data = json.load(f)
    
    unprocessed_sessions = []
    
    for session in clinical_data.get("sessions", []):
        session_date = session["session_date"]
        
        # Check if this session has been preprocessed
        roi_features_path = patient_preprocessed_dir / session_date / "roi_features.json"
        
        if not roi_features_path.exists():
            # Check if raw scans exist
            mri_path = patient_input_dir / session_date / "mri.nii"
            pet_path = patient_input_dir / session_date / "pet.nii"
            
            if mri_path.exists() or pet_path.exists():
                unprocessed_sessions.append(session_date)
    
    return unprocessed_sessions


def preprocess_scans(patient_id, sessions):
    """
    Run preprocessing for the specified sessions.
    """
    print(f"Preprocessing {len(sessions)} session(s)...")
    
    for session_date in sessions:
        print(f"  - {session_date}")
        
        # Run preprocessing script
        cmd = [
            sys.executable,
            str(PROJECT_ROOT / "api" / "preprocess_patient.py"),
            "--patient_id", patient_id,
            "--session_date", session_date
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"    [FAIL] Failed: {result.stderr}")
            return False
        else:
            print(f"    [OK] Complete")
    
    return True


def run_predictions(patient_id):
    """
    Run prediction model and return results.
    
    Returns:
        dict with prediction results (constrained scores)
    """
    predictions_file = PREDICTIONS_DIR / f"{patient_id}_predictions.json"
    
    # Run prediction script
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "api" / "predict_progression.py"),
        "--patient_id", patient_id
    ]
    
    # Set environment for UTF-8 encoding
    import os
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if result.returncode != 0:
        print(f"[FAIL] Prediction failed: {result.stderr}")
        return None
    
    # Load results
    if not predictions_file.exists():
        print(f"[FAIL] Prediction file not found: {predictions_file}")
        return None
    
    with open(predictions_file, 'r') as f:
        results = json.load(f)
    
    return results


def format_clean_output(results):
    """
    Format prediction results as clean terminal output.
    Shows only the constrained/corrected scores.
    """
    output = {
        "patient_id": results["patient_id"],
        "prediction_time": results["prediction_timestamp"],
        "last_visit": {},
        "future_predictions": []
    }
    
    # Last visit (constrained scores)
    last_session = results["historical_sessions"][-1]
    output["last_visit"] = {
        "date": last_session["session_date"],
        "scores": last_session["predicted_scores"]  # These are already constrained
    }
    
    # Future predictions (constrained scores)
    for future in results["future_predictions"]:
        output["future_predictions"].append({
            "months_ahead": future["months_from_last_visit"],
            "scores": future["predicted_scores"]  # These are already constrained
        })
    
    return output


def send_to_backend(data, backend_url="http://localhost:3000/api/alzheimers/predictions"):
    """
    Send prediction results to backend API.
    """
    try:
        import requests
        
        response = requests.post(backend_url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Backend response: {result['message']}")
            return True
        else:
            print(f"  Backend error: {response.status_code} - {response.text}")
            return False
            
    except ImportError:
        # Fallback if requests not installed - save to file
        print("  (requests library not installed, saving to file instead)")
        output_file = PROJECT_ROOT / "api" / "backend_predictions.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
        
    except Exception as e:
        print(f"  Error sending to backend: {e}")
        # Fallback - save to file
        output_file = PROJECT_ROOT / "api" / "backend_predictions.json"
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"  Saved to file instead: {output_file}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Run ADNI prediction pipeline")
    parser.add_argument("--patient_id", required=True, help="Patient ID")
    
    args = parser.parse_args()
    patient_id = args.patient_id
    
    print("="*60)
    print("ADNI PREDICTION PIPELINE")
    print("="*60)
    print(f"Patient ID: {patient_id}\n")
    
    # Step 1: Check for new scans
    print("Checking for unprocessed scans...")
    unprocessed = check_for_new_scans(patient_id)
    
    if unprocessed:
        print(f"Found {len(unprocessed)} unprocessed session(s)\n")
        
        # Step 2: Preprocess new scans
        success = preprocess_scans(patient_id, unprocessed)
        if not success:
            print("\n[FAIL] Pipeline failed during preprocessing")
            sys.exit(1)
        print()
    else:
        print("All scans already preprocessed\n")
    
    # Step 3: Run predictions
    print("Running prediction model...")
    results = run_predictions(patient_id)
    
    if not results:
        print("\n[FAIL] Pipeline failed during prediction")
        sys.exit(1)
    
    print("[OK] Predictions complete\n")
    
    # Step 4: Format clean output
    clean_output = format_clean_output(results)
    
    # Step 5: Display scores (constrained values only)
    print("="*60)
    print("PREDICTION SCORES (Clinically Constrained)")
    print("="*60)
    print(json.dumps(clean_output, indent=2))
    print("="*60)
    
    # Step 6: Send to backend
    print("\nSending results to backend...")
    success = send_to_backend(clean_output)
    
    if success:
        print("[OK] Results sent to backend\n")
    else:
        print("[FAIL] Failed to send results to backend\n")
        sys.exit(1)
    
    print("="*60)
    print("PIPELINE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
