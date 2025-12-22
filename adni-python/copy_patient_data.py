"""
Copy patient data for testing
"""
import shutil
import json
from pathlib import Path
import pandas as pd

# Patient to test
PATIENT_ID = "033S0567"
SESSIONS = ["20061205", "20070607", "20071127", "20080605", "20090615"]

# Paths
RAW_NIFTI = Path("e:/Code/Smart-EHR-System-main/adni-python/outputs/raw_nifti")
INPUT_DIR = Path("e:/Code/Smart-EHR-System-main/adni-python/api/input_data")
ROI_CSV = Path("e:/Code/Smart-EHR-System-main/adni-python/outputs/roi_features.csv")
MASTER_CSV = Path("e:/Code/Smart-EHR-System-main/adni-python/outputs/master_with_roi_features.csv")

# Create patient directory
patient_dir = INPUT_DIR / PATIENT_ID
patient_dir.mkdir(parents=True, exist_ok=True)

print(f"Copying data for patient: {PATIENT_ID}")
print(f"Sessions: {SESSIONS}\n")

# Copy MRI and PET scans
for session in SESSIONS:
    session_dir = patient_dir / session
    session_dir.mkdir(exist_ok=True)
    
    # Source paths
    src_base = RAW_NIFTI / f"sub-{PATIENT_ID}" / f"ses-{session}"
    
    # Find MRI file
    mri_files = list((src_base / "anat").glob("*T1w.nii.gz"))
    if mri_files:
        src_mri = mri_files[0]
        dst_mri = session_dir / "mri.nii.gz"
        shutil.copy2(src_mri, dst_mri)
        print(f"✓ Copied MRI for {session}: {src_mri.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"✗ No MRI found for {session}")
    
    # Find PET file
    pet_files = list((src_base / "pet").glob("*pet.nii.gz"))
    if pet_files:
        src_pet = pet_files[0]
        dst_pet = session_dir / "pet.nii.gz"
        shutil.copy2(src_pet, dst_pet)
        print(f"✓ Copied PET for {session}: {src_pet.stat().st_size / 1024 / 1024:.1f} MB")
    else:
        print(f"✗ No PET found for {session}")

# Load ROI features to get clinical data
df_roi = pd.read_csv(ROI_CSV)
patient_roi = df_roi[df_roi['subject_id'] == PATIENT_ID]

# Load master data
df_master = pd.read_csv(MASTER_CSV)
master_id = PATIENT_ID.replace('S', '_S_')
patient_master = df_master[df_master['subject_id'] == master_id]

print(f"\nFound {len(patient_master)} rows in master data")

# Create clinical data JSON
clinical_data = {
    "patient_id": PATIENT_ID,
    "demographics": {
        "date_of_birth": "1948-01-01",  # Placeholder
        "gender": "Male",
        "education": 16,
        "apoe_genotype": "3/3"
    },
    "sessions": []
}

# Add sessions
for session in SESSIONS:
    session_token = int(session)
    
    # Try to find clinical data
    session_data = patient_master[patient_master['matched_session_token'] == session_token]
    
    if len(session_data) == 0:
        # Use defaults
        session_info = {
            "session_date": session,
            "age": 60.0,
            "gender": "Male",
            "education": 16,
            "apoe4": 0,
            "mmse_score": None,
            "cdr_global": None,
            "cdr_sob": None,
            "adas_totscore": None
        }
    else:
        row = session_data.iloc[0]
        session_info = {
            "session_date": session,
            "age": float(row.get('AGE', 60.0)) if pd.notna(row.get('AGE')) else 60.0,
            "gender": "Male" if row.get('PTGENDER') == 1 else "Female",
            "education": int(row.get('PTEDUCAT', 16)) if pd.notna(row.get('PTEDUCAT')) else 16,
            "apoe4": int(row.get('APOE4', 0)) if pd.notna(row.get('APOE4')) else 0,
            "mmse_score": float(row.get('MMSE_SCORE')) if pd.notna(row.get('MMSE_SCORE')) else None,
            "cdr_global": float(row.get('CDR_GLOBAL')) if pd.notna(row.get('CDR_GLOBAL')) else None,
            "cdr_sob": float(row.get('CDR_SOB')) if pd.notna(row.get('CDR_SOB')) else None,
            "adas_totscore": float(row.get('ADAS_TOTSCORE')) if pd.notna(row.get('ADAS_TOTSCORE')) else None
        }
    
    clinical_data["sessions"].append(session_info)
    print(f"  Session {session}: MMSE={session_info['mmse_score']}, CDR={session_info['cdr_global']}")

# Save clinical data
clinical_file = patient_dir / "clinical_data.json"
with open(clinical_file, 'w') as f:
    json.dump(clinical_data, f, indent=2)

print(f"\n✓ Saved clinical data to {clinical_file}")
print(f"\nPatient {PATIENT_ID} data ready for testing!")
