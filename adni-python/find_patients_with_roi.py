"""
Find patients with complete ROI features and clinical data
"""
import pandas as pd
import numpy as np

# Load ROI features
df_roi = pd.read_csv('e:/Code/Smart-EHR-System-main/adni-python/outputs/roi_features.csv')
print(f"Total ROI feature rows: {len(df_roi)}")
print(f"Unique patients: {df_roi['subject_id'].nunique()}")

# Analyze by patient
patient_visits = df_roi.groupby('subject_id').size().sort_values(ascending=False)
print(f"\nPatients with 3+ visits: {len(patient_visits[patient_visits >= 3])}")
print(f"Patients with 2+ visits: {len(patient_visits[patient_visits >= 2])}")

# Load master data to get clinical scores
df_master = pd.read_csv('e:/Code/Smart-EHR-System-main/adni-python/outputs/master_with_roi_features.csv')
print(f"\nMaster data rows: {len(df_master)}")

# Check which patients in ROI have clinical data
roi_patients = set(df_roi['subject_id'].unique())
master_patients = set(df_master['subject_id'].unique())

print(f"\nPatients in ROI: {len(roi_patients)}")
print(f"Patients in master: {len(master_patients)}")
print(f"Overlap: {len(roi_patients & master_patients)}")

# For patients in ROI, get their clinical data from master
print(f"\n{'='*80}")
print("ANALYZING PATIENTS WITH ROI FEATURES")
print(f"{'='*80}\n")

# Group ROI data by patient
for pid in sorted(patient_visits[patient_visits >= 3].index[:20]):
    patient_roi = df_roi[df_roi['subject_id'] == pid]
    
    print(f"\nPatient: {pid}")
    print(f"  ROI visits: {len(patient_roi)}")
    print(f"  Sessions: {', '.join(patient_roi['session_token'].astype(str).tolist())}")
    
    # Try to find in master (may need normalization)
    # Check if this patient ID exists in master
    master_match = df_master[df_master['subject_id'].str.contains(pid.replace('S', '_S_'), case=False, na=False)]
    
    if len(master_match) > 0:
        sample = master_match.iloc[0]
        print(f"  Found in master as: {sample['subject_id']}")
        print(f"  Age: {sample.get('AGE', 'N/A')}, Gender: {sample.get('PTGENDER', 'N/A')}")
        print(f"  MMSE: {sample.get('MMSE_SCORE', 'N/A')}, CDR: {sample.get('CDR_GLOBAL', 'N/A')}")
    else:
        print(f"  NOT found in master (ID mismatch)")

print(f"\n{'='*80}")
print("RECOMMENDATION: Use these patients from ROI features")
print(f"{'='*80}\n")

# Just use the ROI data directly - we have 64 patients with features
top_patients = patient_visits[patient_visits >= 2].head(20)
print("Top 20 patients with most visits:")
for pid, count in top_patients.items():
    print(f"  {pid}: {count} visits")
