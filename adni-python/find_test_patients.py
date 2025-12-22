"""
Find patients with complete data for testing
"""
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('e:/Code/Smart-EHR-System-main/adni-python/outputs/master_with_roi_features.csv')

print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")

# Check key columns
key_cols = [c for c in df.columns if not c.startswith('mri_roi') and not c.startswith('pet_roi')]
print(f"\nKey columns ({len(key_cols)}):")
for col in key_cols[:30]:
    print(f"  - {col}")

# Check for complete data
print(f"\n{'='*80}")
print("DATA COMPLETENESS ANALYSIS")
print(f"{'='*80}\n")

# Patients with imaging
df_with_imaging = df[(df['has_t1'] == 1) & (df['has_pet'] == 1)].copy()
print(f"Rows with both MRI and PET: {len(df_with_imaging)}")

# Check for ROI features
has_mri_roi = df['mri_roi_001'].notna()
has_pet_roi = df['pet_roi_001'].notna()
df_with_roi = df[has_mri_roi & has_pet_roi].copy()
print(f"Rows with ROI features: {len(df_with_roi)}")

# Check for cognitive scores
has_mmse = df['MMSE_SCORE'].notna()
has_cdr = df['CDR_GLOBAL'].notna()
has_adas = df['ADAS_TOTSCORE'].notna()

df_complete = df[has_mri_roi & has_pet_roi & (has_mmse | has_cdr | has_adas)].copy()
print(f"Rows with ROI + at least one score: {len(df_complete)}")

# Group by patient
patient_counts = df_complete.groupby('subject_id').size()
patients_with_multiple = patient_counts[patient_counts >= 2]
print(f"\nPatients with 2+ complete visits: {len(patients_with_multiple)}")

# Check diagnosis if available
if 'DXNORM' in df.columns:
    dx_col = 'DXNORM'
elif 'DX' in df.columns:
    dx_col = 'DX'
else:
    dx_col = None

if dx_col:
    print(f"\nDiagnosis distribution ({dx_col}):")
    print(df_complete[dx_col].value_counts())

# Find patients by CDR stage (proxy for Alzheimer's stage)
print(f"\n{'='*80}")
print("PATIENTS BY CDR STAGE (Alzheimer's Severity)")
print(f"{'='*80}\n")

# CDR stages:
# 0 = Normal
# 0.5 = Very Mild / MCI
# 1 = Mild AD
# 2 = Moderate AD
# 3 = Severe AD

for cdr_stage in [0, 0.5, 1, 2, 3]:
    stage_df = df_complete[df_complete['CDR_GLOBAL'] == cdr_stage]
    stage_patients = stage_df.groupby('subject_id').size()
    stage_patients_multi = stage_patients[stage_patients >= 2]
    
    if cdr_stage == 0:
        stage_name = "Normal (CDR=0)"
    elif cdr_stage == 0.5:
        stage_name = "Very Mild / MCI (CDR=0.5)"
    elif cdr_stage == 1:
        stage_name = "Mild AD (CDR=1)"
    elif cdr_stage == 2:
        stage_name = "Moderate AD (CDR=2)"
    else:
        stage_name = "Severe AD (CDR=3)"
    
    print(f"\n{stage_name}:")
    print(f"  Total visits: {len(stage_df)}")
    print(f"  Patients with 2+ visits: {len(stage_patients_multi)}")
    
    if len(stage_patients_multi) > 0:
        # Show top 5 patients
        top_patients = stage_patients_multi.nlargest(5)
        print(f"  Top patients:")
        for pid, count in top_patients.items():
            patient_data = df_complete[df_complete['subject_id'] == pid]
            visits = patient_data['visit'].unique()
            mmse_range = patient_data['MMSE_SCORE'].dropna()
            cdr_range = patient_data['CDR_GLOBAL'].dropna()
            
            print(f"    - {pid}: {count} visits")
            print(f"      Visits: {', '.join(sorted(visits)[:5])}")
            if len(mmse_range) > 0:
                print(f"      MMSE range: {mmse_range.min():.1f} - {mmse_range.max():.1f}")
            if len(cdr_range) > 0:
                print(f"      CDR range: {cdr_range.min():.1f} - {cdr_range.max():.1f}")

# Save selected patients
print(f"\n{'='*80}")
print("SELECTING 5 PATIENTS PER STAGE")
print(f"{'='*80}\n")

selected_patients = {}

for cdr_stage in [0, 0.5, 1, 2]:
    stage_df = df_complete[df_complete['CDR_GLOBAL'] == cdr_stage]
    stage_patients = stage_df.groupby('subject_id').size()
    stage_patients_multi = stage_patients[stage_patients >= 3]  # At least 3 visits
    
    if len(stage_patients_multi) >= 5:
        selected = stage_patients_multi.nlargest(5).index.tolist()
    else:
        selected = stage_patients_multi.index.tolist()
    
    selected_patients[cdr_stage] = selected

# Print selected patients
for cdr_stage, patients in selected_patients.items():
    if cdr_stage == 0:
        stage_name = "Normal"
    elif cdr_stage == 0.5:
        stage_name = "MCI"
    elif cdr_stage == 1:
        stage_name = "Mild AD"
    else:
        stage_name = "Moderate AD"
    
    print(f"\n{stage_name} (CDR={cdr_stage}): {len(patients)} patients")
    for pid in patients:
        patient_data = df_complete[df_complete['subject_id'] == pid]
        print(f"\n  Patient ID: {pid}")
        print(f"  Total visits: {len(patient_data)}")
        print(f"  Visit dates: {', '.join(sorted(patient_data['visit'].unique())[:10])}")
        
        # Show sample data
        sample = patient_data.iloc[0]
        print(f"  Sample data:")
        print(f"    Age: {sample.get('AGE', 'N/A')}")
        print(f"    Gender: {sample.get('PTGENDER', 'N/A')}")
        print(f"    Education: {sample.get('PTEDUCAT', 'N/A')}")
        print(f"    APOE4: {sample.get('APOE4', 'N/A')}")
        print(f"    MMSE: {sample.get('MMSE_SCORE', 'N/A')}")
        print(f"    CDR: {sample.get('CDR_GLOBAL', 'N/A')}")
        print(f"    ADAS: {sample.get('ADAS_TOTSCORE', 'N/A')}")

print(f"\n{'='*80}")
print("ANALYSIS COMPLETE")
print(f"{'='*80}\n")
