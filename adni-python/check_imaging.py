import pandas as pd

# Load data
df = pd.read_csv('e:/Code/Smart-EHR-System-main/adni-python/outputs/master_with_roi_features.csv')

print("Checking imaging availability...")
imaging_df = df[(df['has_t1'] == 1) & (df['has_pet'] == 1)]
print(f"Rows with imaging flags: {len(imaging_df)}")
print(f"Unique patients: {imaging_df['subject_id'].nunique()}")

print("\nPatients with most visits:")
patient_counts = imaging_df.groupby('subject_id').size().sort_values(ascending=False)
print(patient_counts.head(20))

print("\nChecking CDR distribution for patients with imaging:")
cdr_dist = imaging_df['CDR_GLOBAL'].value_counts().sort_index()
print(cdr_dist)

print("\nFinding patients by CDR stage:")
for cdr in [0, 0.5, 1, 2]:
    stage_df = imaging_df[imaging_df['CDR_GLOBAL'] == cdr]
    patients = stage_df.groupby('subject_id').size()
    patients_multi = patients[patients >= 2]
    print(f"\nCDR={cdr}: {len(patients_multi)} patients with 2+ visits")
    if len(patients_multi) > 0:
        top5 = patients_multi.nlargest(5)
        for pid, count in top5.items():
            print(f"  {pid}: {count} visits")
