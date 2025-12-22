"""
Preprocess all sessions for a patient
"""
import subprocess
import sys
from pathlib import Path

PATIENT_ID = "033S0567"
SESSIONS = ["20061205", "20070607", "20071127", "20080605", "20090615"]

print(f"Preprocessing all sessions for patient {PATIENT_ID}")
print(f"Total sessions: {len(SESSIONS)}\n")

for i, session in enumerate(SESSIONS, 1):
    print(f"\n{'='*80}")
    print(f"[{i}/{len(SESSIONS)}] Processing session: {session}")
    print(f"{'='*80}\n")
    
    # Check if already preprocessed
    roi_path = Path(f"api/preprocessed_data/{PATIENT_ID}/{session}/roi_features.json")
    if roi_path.exists():
        print(f"✓ Session {session} already preprocessed, skipping...")
        continue
    
    # Run preprocessing
    cmd = [
        sys.executable,
        "api/preprocess_patient.py",
        "--patient_id", PATIENT_ID,
        "--session_date", session
    ]
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n✗ ERROR: Preprocessing failed for session {session}")
        sys.exit(1)
    
    print(f"\n✓ Session {session} completed")

print(f"\n{'='*80}")
print(f"✓ ALL SESSIONS PREPROCESSED!")
print(f"{'='*80}\n")

print("Now run: python api/predict_progression.py --patient_id 033S0567")
