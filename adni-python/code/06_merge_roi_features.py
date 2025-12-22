# E:\adni_python\code\06_merge_roi_features.py
"""
Merge extracted ROI features with the master clinical dataset.

Inputs:
    - outputs/master_with_imaging_match.csv (clinical data + imaging flags)
    - outputs/roi_features.csv (extracted ROI features)
    
Outputs:
    - outputs/master_with_roi_features.csv (complete dataset for model training)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from data_config import MATCHED_OUT

# Paths
BASE = Path(r"E:\adni_python")
ROI_CSV = BASE / "outputs" / "roi_features.csv"
OUTPUT_CSV = BASE / "outputs" / "master_with_roi_features.csv"

def normalize_subject_id(sid):
    """Normalize subject ID format."""
    if pd.isna(sid):
        return None
    s = str(sid).strip().replace("_", "")
    if len(s) == 8 and s[3] in ['S', 's']:
        return f"{s[:3]}_S_{s[4:]}"
    return sid

def normalize_session(ses):
    """Normalize session token."""
    if pd.isna(ses):
        return None
    return str(ses).strip()

def main():
    print("=" * 80)
    print("Merging ROI Features with Master Dataset")
    print("=" * 80)
    
    # Load master dataset
    if not MATCHED_OUT.exists():
        print(f"ERROR: Master dataset not found: {MATCHED_OUT}")
        sys.exit(1)
    
    print(f"\nLoading master dataset: {MATCHED_OUT}")
    master = pd.read_csv(MATCHED_OUT, low_memory=False)
    print(f"  Master shape: {master.shape}")
    
    # Load ROI features
    if not ROI_CSV.exists():
        print(f"ERROR: ROI features not found: {ROI_CSV}")
        print("Please run 05_extract_roi_features.py first.")
        sys.exit(1)
    
    print(f"\nLoading ROI features: {ROI_CSV}")
    roi = pd.read_csv(ROI_CSV)
    print(f"  ROI shape: {roi.shape}")
    
    # Normalize IDs for merging
    print("\nNormalizing subject IDs and session tokens...")
    master['subject_id_norm'] = master['subject_id'].apply(normalize_subject_id)
    master['session_norm'] = master['matched_session_token'].apply(normalize_session)
    
    roi['subject_id_norm'] = roi['subject_id'].apply(normalize_subject_id)
    roi['session_norm'] = roi['session_token'].apply(normalize_session)
    
    # Merge on normalized IDs
    print("\nMerging datasets...")
    merged = master.merge(
        roi,
        on=['subject_id_norm', 'session_norm'],
        how='left',
        suffixes=('', '_roi')
    )
    
    # Drop temporary normalization columns
    merged = merged.drop(columns=['subject_id_norm', 'session_norm', 'subject_id_roi', 'session_token'], errors='ignore')
    
    print(f"  Merged shape: {merged.shape}")
    
    # Check how many rows have ROI features
    mri_cols = [f'mri_roi_{i:03d}' for i in range(1, 94)]
    pet_cols = [f'pet_roi_{i:03d}' for i in range(1, 94)]
    
    has_mri = merged[mri_cols[0]].notna().sum()
    has_pet = merged[pet_cols[0]].notna().sum()
    
    print(f"\nROI Feature Coverage:")
    print(f"  Rows with MRI ROI features: {has_mri} / {len(merged)} ({100*has_mri/len(merged):.1f}%)")
    print(f"  Rows with PET ROI features: {has_pet} / {len(merged)} ({100*has_pet/len(merged):.1f}%)")
    
    # Save merged dataset
    merged.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\n✓ Saved merged dataset to: {OUTPUT_CSV}")
    print(f"✓ Final shape: {merged.shape}")
    print(f"✓ Columns added: {len(mri_cols) + len(pet_cols)} ROI features (93 MRI + 93 PET)")
    print("=" * 80)

if __name__ == "__main__":
    main()
