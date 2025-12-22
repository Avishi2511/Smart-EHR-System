# E:\adni_python\code\05_extract_roi_features.py
"""
Extract 93-dimensional ROI features from preprocessed MRI and PET derivatives.
Uses AAL atlas to define regions of interest.

Inputs:
    - Preprocessed derivatives in outputs/derivatives/
    - AAL atlas in atlas/atlases/atlas_aal.nii.gz
    
Outputs:
    - outputs/roi_features.csv with columns:
      - subject_id, session_token
      - mri_roi_001 through mri_roi_093 (gray matter volumes)
      - pet_roi_001 through pet_roi_093 (SUVR values)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import nibabel as nib
import ants

# Add code directory to path
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from config import OUTPUT_DERIV, ATLAS_DIR

# Paths
AAL_ATLAS_PATH = ATLAS_DIR / "atlases" / "atlas_aal.nii.gz"
OUTPUT_CSV = OUTPUT_DERIV.parent / "roi_features.csv"

def extract_roi_features_from_atlas(image_path, atlas_in_subject_space, num_rois=93):
    """
    Extract mean values per ROI from an image using an atlas.
    
    Args:
        image_path: Path to the image (e.g., t1_brain.nii.gz or pet_suvr_in_t1.nii.gz)
        atlas_in_subject_space: ANTs image of atlas registered to subject space
        num_rois: Number of ROIs in atlas (default 93 for AAL)
    
    Returns:
        numpy array of shape (num_rois,) with mean values per ROI
    """
    # Load image
    img = ants.image_read(str(image_path))
    img_data = img.numpy()
    atlas_data = atlas_in_subject_space.numpy()
    
    # Extract features for each ROI
    features = np.zeros(num_rois, dtype=np.float32)
    
    for roi_idx in range(1, num_rois + 1):  # ROIs are labeled 1-93
        mask = (atlas_data == roi_idx)
        if mask.sum() > 0:
            features[roi_idx - 1] = float(img_data[mask].mean())
        else:
            features[roi_idx - 1] = np.nan
    
    return features

def register_atlas_to_subject(t1_brain_path, atlas_mni_path):
    """
    Register AAL atlas from MNI space to subject T1 space.
    
    Args:
        t1_brain_path: Path to subject's T1 brain
        atlas_mni_path: Path to AAL atlas in MNI space
    
    Returns:
        ANTs image of atlas in subject space
    """
    # Load images
    t1 = ants.image_read(str(t1_brain_path))
    atlas_mni = ants.image_read(str(atlas_mni_path))
    
    # For AAL atlas, we need MNI template as reference
    # The atlas is already in MNI space, so we register T1 to MNI, then warp atlas back
    from config import ATLAS_DIR
    mni_template = ATLAS_DIR / "templates" / "MNI152_T1_1mm_brain.nii.gz"
    
    if not mni_template.exists():
        raise FileNotFoundError(f"MNI template not found: {mni_template}")
    
    mni = ants.image_read(str(mni_template))
    
    # Register T1 to MNI
    print(f"  Registering T1 to MNI...")
    reg = ants.registration(fixed=mni, moving=t1, type_of_transform='SyN')
    
    # Warp atlas from MNI to subject T1 space (using inverse transforms)
    print(f"  Warping atlas to subject space...")
    atlas_in_t1 = ants.apply_transforms(
        fixed=t1,
        moving=atlas_mni,
        transformlist=reg['invtransforms'],
        interpolator='nearestNeighbor'
    )
    
    return atlas_in_t1

def process_one_session(subject_id, session_token):
    """
    Extract ROI features for one subject-session pair.
    
    Returns:
        dict with subject_id, session_token, and ROI features, or None if failed
    """
    # Subject ID is already in correct format (e.g., 007S0101)
    subshort = subject_id
    
    # Paths to derivatives
    deriv_dir = OUTPUT_DERIV / f"sub-{subshort}" / f"ses-{session_token}"
    t1_brain = deriv_dir / "t1_brain.nii.gz"
    pet_suvr = deriv_dir / "pet_suvr_in_t1.nii.gz"
    
    # Check if files exist
    if not t1_brain.exists():
        print(f"  Missing T1 brain: {t1_brain}")
        return None
    
    if not pet_suvr.exists():
        print(f"  Missing PET SUVR: {pet_suvr}")
        return None
    
    print(f"[{subject_id} / {session_token}] Extracting ROI features...")
    
    try:
        # Register atlas to subject space
        atlas_in_t1 = register_atlas_to_subject(t1_brain, AAL_ATLAS_PATH)
        
        # Extract MRI features (gray matter volumes)
        print(f"  Extracting MRI ROI features...")
        mri_features = extract_roi_features_from_atlas(t1_brain, atlas_in_t1)
        
        # Extract PET features (SUVR values)
        print(f"  Extracting PET ROI features...")
        pet_features = extract_roi_features_from_atlas(pet_suvr, atlas_in_t1)
        
        # Build result dictionary
        result = {
            'subject_id': subject_id,
            'session_token': session_token
        }
        
        # Add MRI ROI features
        for i in range(93):
            result[f'mri_roi_{i+1:03d}'] = mri_features[i]
        
        # Add PET ROI features
        for i in range(93):
            result[f'pet_roi_{i+1:03d}'] = pet_features[i]
        
        print(f"  ✓ Successfully extracted {len(mri_features)} MRI + {len(pet_features)} PET features")
        return result
        
    except Exception as e:
        print(f"  ✗ Error processing {subject_id}/{session_token}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main function to extract ROI features for all subjects with derivatives.
    """
    print("=" * 80)
    print("ROI Feature Extraction")
    print("=" * 80)
    
    # Check if AAL atlas exists
    if not AAL_ATLAS_PATH.exists():
        print(f"ERROR: AAL atlas not found at {AAL_ATLAS_PATH}")
        print("Please ensure the atlas file is in the correct location.")
        sys.exit(1)
    
    print(f"\nAAL Atlas: {AAL_ATLAS_PATH}")
    print(f"Derivatives: {OUTPUT_DERIV}")
    print(f"Output CSV: {OUTPUT_CSV}")
    
    # Find all subject-session pairs with derivatives
    sessions = []
    if not OUTPUT_DERIV.exists():
        print(f"ERROR: Derivatives directory not found: {OUTPUT_DERIV}")
        sys.exit(1)
    
    for sub_dir in OUTPUT_DERIV.glob("sub-*"):
        if not sub_dir.is_dir():
            continue
        for ses_dir in sub_dir.glob("ses-*"):
            if not ses_dir.is_dir():
                continue
            # Keep subject ID as-is from folder name (e.g., 007S0101)
            subject_id = sub_dir.name.replace("sub-", "")
            session_token = ses_dir.name.replace("ses-", "")
            sessions.append((subject_id, session_token))
    
    print(f"\nFound {len(sessions)} subject-session pairs with derivatives")
    
    if len(sessions) == 0:
        print("No derivatives found. Please run 04_preprocess.py first.")
        sys.exit(1)
    
    # Process each session
    results = []
    for i, (subject_id, session_token) in enumerate(sessions, 1):
        print(f"\n[{i}/{len(sessions)}] Processing {subject_id} / {session_token}")
        result = process_one_session(subject_id, session_token)
        if result is not None:
            results.append(result)
    
    # Save to CSV
    if len(results) == 0:
        print("\n✗ No ROI features extracted. Check errors above.")
        sys.exit(1)
    
    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)
    
    print("\n" + "=" * 80)
    print(f"✓ Successfully extracted ROI features for {len(results)}/{len(sessions)} sessions")
    print(f"✓ Saved to: {OUTPUT_CSV}")
    print(f"✓ Shape: {df.shape} (rows x columns)")
    print(f"✓ Columns: subject_id, session_token, mri_roi_001-093, pet_roi_001-093")
    print("=" * 80)

if __name__ == "__main__":
    main()
