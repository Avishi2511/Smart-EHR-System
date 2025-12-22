from pathlib import Path
import numpy as np
import nibabel as nib

PROJECT = Path(r"E:\adni_python")
AAL_PATH = PROJECT / "atlas" / "atlases" / "atlas_aal.nii.gz"  # adjust if filename differs
OUT_MASK = PROJECT / "atlas" / "cereb_gm_mask_mni.nii.gz"

# Cerebellar gray-matter labels for AAL build (four-digit codes)
AAL_CEREB_GM_IDS = [
    9001, 9011, 9021, 9031, 9041, 9051, 9061, 9071, 9081,  # left
    9002, 9012, 9022, 9032, 9042, 9052, 9062, 9072, 9082   # right
]

def main():
    img = nib.load(str(AAL_PATH))
    data = img.get_fdata()
    mask = np.isin(data, AAL_CEREB_GM_IDS).astype(np.uint8)

    if mask.sum() == 0:
        uniq = np.unique(data.astype(np.int32))
        print("Mask is empty. Unique labels (first 200):")
        print(uniq[:200])
        return

    nib.save(nib.Nifti1Image(mask, img.affine, img.header), str(OUT_MASK))
    print(f"Saved cerebellar GM mask: {OUT_MASK} | voxels: {int(mask.sum())}")

if __name__ == "__main__":
    main()
