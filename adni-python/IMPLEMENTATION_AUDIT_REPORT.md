# ADNI Implementation Audit Report

## Executive Summary

This document audits the **actual implementation** of the ADNI pipeline to verify what's really happening vs. what was documented.

**Date**: 2024-12-21  
**Auditor**: Code Analysis  
**Status**: ⚠️ **MIXED - Two versions exist**

---

## 1. CRITICAL FINDINGS

### 🔴 **Finding #1: TWO VERSIONS OF ROI EXTRACTION EXIST**

**Location**: `code/` directory

**Version A: `05_extract_roi_features.py`** (FULL, SLOW)
- ✅ **Uses REAL atlas registration**
- ✅ **True anatomical ROIs** (93 regions from AAL atlas)
- ⚠️ **Time**: ~10-15 minutes per session
- ✅ **Accuracy**: High (anatomically meaningful features)

**Version B: `05_extract_roi_features_FAST.py`** (SIMPLIFIED, FAST)
- ❌ **NO atlas registration**
- ❌ **Pseudo-ROIs** (spatial statistics, not anatomical)
- ✅ **Time**: ~1-2 seconds per session
- ⚠️ **Accuracy**: Lower (statistical features, not anatomical)

---

## 2. DETAILED ANALYSIS

### 2.1 Version A: Full Atlas Registration (`05_extract_roi_features.py`)

**What it does**:
```python
def register_atlas_to_subject(t1_brain_path, atlas_mni_path):
    """
    Register AAL atlas from MNI space to subject T1 space.
    """
    # Load images
    t1 = ants.image_read(str(t1_brain_path))
    atlas_mni = ants.image_read(str(atlas_mni_path))
    mni = ants.image_read(str(mni_template))
    
    # ✅ REAL REGISTRATION: Register T1 to MNI
    print(f"  Registering T1 to MNI...")
    reg = ants.registration(fixed=mni, moving=t1, type_of_transform='SyN')
    
    # ✅ REAL WARPING: Warp atlas from MNI to subject T1 space
    print(f"  Warping atlas to subject space...")
    atlas_in_t1 = ants.apply_transforms(
        fixed=t1,
        moving=atlas_mni,
        transformlist=reg['invtransforms'],
        interpolator='nearestNeighbor'
    )
    
    return atlas_in_t1

def extract_roi_features_from_atlas(image_path, atlas_in_subject_space, num_rois=93):
    """
    Extract mean values per ROI from an image using an atlas.
    """
    img = ants.image_read(str(image_path))
    img_data = img.numpy()
    atlas_data = atlas_in_subject_space.numpy()
    
    features = np.zeros(num_rois, dtype=np.float32)
    
    # ✅ REAL ROI EXTRACTION: Loop through each anatomical region
    for roi_idx in range(1, num_rois + 1):  # ROIs are labeled 1-93
        mask = (atlas_data == roi_idx)
        if mask.sum() > 0:
            features[roi_idx - 1] = float(img_data[mask].mean())
        else:
            features[roi_idx - 1] = np.nan
    
    return features
```

**Verdict**: ✅ **THIS IS THE REAL DEAL**
- Uses ANTs SyN registration (non-linear, accurate)
- Warps AAL atlas to subject space
- Extracts true anatomical ROI features
- **Time**: ~10-15 minutes per session
- **Quality**: High (research-grade)

---

### 2.2 Version B: Simplified Pseudo-ROIs (`05_extract_roi_features_FAST.py`)

**What it does**:
```python
def extract_roi_features_simple(image_path, num_rois=93):
    """
    Extract simple features from image WITHOUT atlas registration.
    Uses spatial statistics as proxy for ROI features.
    
    ❌ This is a simplified version for faster processing.
    """
    img = nib.load(str(image_path))
    data = img.get_fdata().astype(np.float32)
    
    features = np.zeros(num_rois, dtype=np.float32)
    
    # ❌ NO ATLAS REGISTRATION!
    # Instead, use spatial partitioning and statistics
    
    mask = data > 0
    masked_data = data[mask]
    
    # Generate 93 features using:
    for i in range(num_rois):
        if i < 20:
            # ❌ Percentile-based features (not anatomical)
            percentile = (i / 20) * 100
            features[i] = np.percentile(masked_data, percentile)
        elif i < 40:
            # ❌ Mean of different intensity ranges (not anatomical)
            idx = i - 20
            low = idx / 20
            high = (idx + 1) / 20
            low_val = np.percentile(masked_data, low * 100)
            high_val = np.percentile(masked_data, high * 100)
            range_mask = (data >= low_val) & (data < high_val)
            if range_mask.sum() > 0:
                features[i] = data[range_mask].mean()
        else:
            # ❌ Spatial slice statistics (not anatomical)
            idx = i - 40
            axis = idx % 3
            slice_idx = (idx // 3) % 17
            
            # Get slice along axis
            if axis == 0:
                slice_data = data[slice_idx * data.shape[0] // 17, :, :]
            elif axis == 1:
                slice_data = data[:, slice_idx * data.shape[1] // 17, :]
            else:
                slice_data = data[:, :, slice_idx * data.shape[2] // 17]
            
            if slice_data.sum() > 0:
                features[i] = slice_data[slice_data > 0].mean()
    
    return features
```

**Verdict**: ❌ **THIS IS A SHORTCUT**
- **NO atlas registration**
- **NO anatomical meaning**
- Features are:
  - 20 percentile values (0-100%)
  - 20 intensity range means
  - 53 spatial slice statistics
- **Time**: ~1-2 seconds per session
- **Quality**: Low (not anatomically meaningful)

**Comment in code**:
```python
# Line 126:
print("Note: This uses simplified spatial features, not true atlas-based ROIs")
```

---

## 3. MODEL IMPLEMENTATION AUDIT

### 3.1 Model Architecture (`run_all_seq_FIXED.py`)

**Multi-Modal Fusion**:
```python
class FusionDegradation(nn.Module):
    def __init__(self, d_in, d_latent, out_slices):
        """
        Args:
            d_in: Total input dimension (193)
            d_latent: Latent representation dimension (64)
            out_slices: List of output dimensions [93, 93, 7]
        """
        super().__init__()
        # ✅ Encoder: 193 → 256 → 128 → 64
        self.enc = nn.Sequential(
            nn.Linear(d_in, 256), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, d_latent)
        )
        # ✅ Decoders: 3 separate networks for MRI, PET, Demographics
        self.decoders = nn.ModuleList([
            nn.Sequential(nn.Linear(d_latent, 128), nn.ReLU(), nn.Linear(128, dm))
            for dm in out_slices  # [93, 93, 7]
        ])
```

**Verdict**: ✅ **CORRECT** - Matches paper's multi-modal fusion design

---

### 3.2 Temporal Derivatives (Equation 9)

**Implementation**:
```python
class ModelFillingLSTM(nn.Module):
    def __init__(self, d_in, d_latent, d_targets, d_hidden=128, num_layers=1):
        super().__init__()
        self.fusion = FusionDegradation(d_in, d_latent, [93, 93, 7])
        self.lstm = nn.LSTM(input_size=d_latent + d_targets, 
                           hidden_size=d_hidden, 
                           num_layers=num_layers, 
                           batch_first=True)
        self.pred_targets = nn.Linear(d_hidden, d_targets)
        
        # ✅ FIX: Dense layer for Model Filling (Equation 9)
        self.dense_layer = nn.Linear(d_hidden, d_latent + d_targets)
    
    def forward(self, X, Xmask, Y, Ymask, seq_mask):
        """
        Implements Equation (9): s̃_t = z_{t-1} * W_d + s_{t-1}
        """
        # ... (fusion code)
        
        for t in range(T):
            s_t = torch.cat([Henc[:, t], Y[:, t]], dim=-1)
            
            if t == 0:
                s_hat = s_t  # First timestep: use actual
            else:
                # ✅ Equation (9): s̃_t = z_{t-1} * W_d + s_{t-1}
                z_prev = h_state[0][-1]  # Hidden state from previous timestep
                s_tilde = self.dense_layer(z_prev) + s_prev  # ← THE KEY FIX!
                
                # Imputation: ŝ_t = δ_t ⊙ s_t + (1 - δ_t) ⊙ s̃_t
                s_hat = mask_t * s_t + (1 - mask_t) * s_tilde
            
            # Feed into LSTM
            lstm_in = s_hat.unsqueeze(1)
            lstm_out, h_state = self.lstm(lstm_in, h_state)
            
            outputs.append(lstm_out.squeeze(1))
            s_prev = s_hat  # ✅ Save for next timestep's derivative
```

**Verdict**: ✅ **CORRECT** - Properly implements temporal derivatives

**Key Fix Verified**:
- Line 275: `s_tilde = self.dense_layer(z_prev) + s_prev`
- The `+ s_prev` term is the **temporal derivative**
- This was missing in earlier versions

---

### 3.3 Feature Assembly

**Input Features** (193 dimensions):
```python
def assemble_features(df):
    """
    Assemble multi-modal features: MRI ROIs (93) + PET ROIs (93) + Demographics (7)
    Total: 193 dimensions
    """
    feats = []
    
    # ✅ MRI ROI features (93 dimensions)
    for i in range(1, 94):
        col = f"mri_roi_{i:03d}"
        x = df.get(col, pd.Series([np.nan]*len(df))).astype(float)
        feats.append(x.values[:,None])
    
    # ✅ PET ROI features (93 dimensions)
    for i in range(1, 94):
        col = f"pet_roi_{i:03d}"
        x = df.get(col, pd.Series([np.nan]*len(df))).astype(float)
        feats.append(x.values[:,None])
    
    # ✅ Demographics (7 dimensions)
    # 1. Age
    age = df.get("AGE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(age.values[:,None])
    
    # 2. Gender
    g = df.get("PTGENDER", pd.Series([np.nan]*len(df))).apply(gender_bin)
    feats.append(g.values[:,None])
    
    # 3. Education
    edu = df.get("PTEDUCAT", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(edu.values[:,None])
    
    # 4. APOE4 count
    apoe = df.get("APOE4", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(apoe.values[:,None])
    
    # 5-7. Baseline scores (MMSE, CDR, ADAS)
    mmse_bl = df.get("MMSE_SCORE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(mmse_bl.values[:,None])
    
    cdr_bl = df.get("CDR_GLOBAL", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(cdr_bl.values[:,None])
    
    adas_bl = df.get("ADAS_TOTSCORE", pd.Series([np.nan]*len(df))).astype(float)
    feats.append(adas_bl.values[:,None])
    
    # Concatenate all features
    X = np.concatenate(feats, axis=1).astype(np.float32)  # (N, 193)
```

**Verdict**: ✅ **CORRECT** - Properly assembles 193-dimensional feature vector

---

## 4. WHICH VERSION IS BEING USED?

### 4.1 Check Dependencies

**In `run_all_seq_FIXED.py`**:
```python
# Line 31:
CSV_PATH = Path(r"E:\adni_python\outputs\master_with_roi_features.csv")

# Line 391-395:
if __name__ == "__main__":
    if not CSV_PATH.exists():
        print("CSV not found. Expected:", CSV_PATH)
        print("\nPlease run the following scripts first:")
        print("1. python code/05_extract_roi_features.py")  # ← FULL VERSION!
        print("2. python code/06_merge_roi_features.py")
        sys.exit(1)
```

**Verdict**: 🟡 **AMBIGUOUS**
- The model **expects** output from `05_extract_roi_features.py` (full version)
- But **both versions** write to the same CSV file
- **Whichever was run last** determines the feature quality

---

## 5. PERFORMANCE IMPLICATIONS

### 5.1 If Using Full Version (`05_extract_roi_features.py`)

**Preprocessing Time**:
- N4 correction: 2-3 min
- Brain extraction: 3-5 min
- PET registration: 1-2 min
- SUVR: 30 sec
- **Atlas registration**: 5-10 min ⚠️
- ROI extraction: 30 sec
- **Total**: ~15-20 minutes per session

**Feature Quality**:
- ✅ True anatomical ROIs (hippocampus, amygdala, etc.)
- ✅ Clinically interpretable
- ✅ Research-grade accuracy

---

### 5.2 If Using Fast Version (`05_extract_roi_features_FAST.py`)

**Preprocessing Time**:
- N4 correction: 2-3 min
- Brain extraction: 3-5 min
- PET registration: 1-2 min
- SUVR: 30 sec
- **Pseudo-ROI extraction**: 1-2 sec ✅
- **Total**: ~7-10 minutes per session

**Feature Quality**:
- ❌ NOT anatomical ROIs
- ❌ NOT clinically interpretable
- ⚠️ Statistical proxies (percentiles, slices)
- ⚠️ May still work for prediction (model learns patterns)

---

## 6. RECOMMENDATIONS

### 6.1 For Production Deployment

**Use**: `05_extract_roi_features.py` (FULL VERSION)

**Reasons**:
1. ✅ True anatomical features
2. ✅ Clinically interpretable (can explain predictions)
3. ✅ Matches research paper methodology
4. ✅ Higher quality predictions
5. ✅ Can map to specific brain regions

**Trade-off**: Accept 15-20 min preprocessing time (run as background job)

---

### 6.2 For Development/Testing

**Use**: `05_extract_roi_features_FAST.py` (FAST VERSION)

**Reasons**:
1. ✅ Much faster (1-2 sec vs 10-15 min)
2. ✅ Good for rapid prototyping
3. ✅ Can still train model (features have some signal)
4. ⚠️ Lower quality, but faster iteration

**Trade-off**: Accept lower feature quality for speed

---

### 6.3 Hybrid Approach (Recommended)

**Strategy**:
1. **Development**: Use FAST version for quick iterations
2. **Production**: Use FULL version for deployment
3. **Cloud**: Run FULL version as background job (see cloud architecture doc)

---

## 7. VERIFICATION CHECKLIST

To verify which version was used for your current model:

### ✅ Check 1: Look at CSV file
```python
import pandas as pd
df = pd.read_csv("E:/adni_python/outputs/roi_features.csv")

# Check if features look anatomical or statistical
print(df[['mri_roi_001', 'mri_roi_002', 'mri_roi_003']].head())

# Anatomical features: Should vary significantly between subjects
# Statistical features: May show patterns (percentiles are ordered)
```

### ✅ Check 2: Check processing logs
```bash
# Look for this message in logs:
"Registering T1 to MNI..."  # ← FULL version
"Warping atlas to subject space..."  # ← FULL version

# vs

"Note: This uses simplified spatial features"  # ← FAST version
```

### ✅ Check 3: Check file timestamps
```python
from pathlib import Path
roi_csv = Path("E:/adni_python/outputs/roi_features.csv")
print(f"Last modified: {roi_csv.stat().st_mtime}")

# Compare with script modification times
full_script = Path("E:/adni_python/code/05_extract_roi_features.py")
fast_script = Path("E:/adni_python/code/05_extract_roi_features_FAST.py")
```

---

## 8. SUMMARY TABLE

| Aspect | Full Version | Fast Version | Model Code |
|--------|-------------|--------------|------------|
| **Atlas Registration** | ✅ YES (SyN) | ❌ NO | N/A |
| **Anatomical ROIs** | ✅ YES (93 AAL) | ❌ NO (pseudo) | Expects 93 |
| **Processing Time** | ⚠️ 15-20 min | ✅ 1-2 sec | N/A |
| **Feature Quality** | ✅ High | ⚠️ Low | N/A |
| **Interpretability** | ✅ High | ❌ Low | N/A |
| **Temporal Derivatives** | N/A | N/A | ✅ CORRECT |
| **Multi-Modal Fusion** | N/A | N/A | ✅ CORRECT |
| **Model Architecture** | N/A | N/A | ✅ CORRECT |

---

## 9. FINAL VERDICT

### ✅ **Model Implementation: CORRECT**
- Temporal derivatives (Equation 9): ✅ Properly implemented
- Multi-modal fusion: ✅ Correct architecture
- Feature assembly: ✅ Expects 193 dims (93 MRI + 93 PET + 7 demo)

### ⚠️ **ROI Extraction: TWO VERSIONS**
- **Full version** (`05_extract_roi_features.py`): ✅ Real atlas registration
- **Fast version** (`05_extract_roi_features_FAST.py`): ❌ Pseudo-ROIs

### 🔴 **CRITICAL QUESTION**
**Which version was used to generate `master_with_roi_features.csv`?**

**To find out**:
1. Check the CSV file for feature patterns
2. Check processing logs
3. Re-run the full version to ensure production quality

---

## 10. ACTION ITEMS

### Immediate
- [ ] Verify which ROI extraction version was used
- [ ] If FAST version was used, re-run with FULL version
- [ ] Update documentation to clarify which version to use

### Short-term
- [ ] Rename files for clarity:
  - `05_extract_roi_features.py` → `05_extract_roi_features_FULL.py`
  - `05_extract_roi_features_FAST.py` → `05_extract_roi_features_FAST_TESTING_ONLY.py`
- [ ] Add warning in FAST version header
- [ ] Create wrapper script that chooses version based on environment

### Long-term
- [ ] Implement cloud-native preprocessing (see cloud architecture doc)
- [ ] Run FULL version as background job
- [ ] Cache preprocessed features for fast prediction

---

**Report Generated**: 2024-12-21  
**Status**: ⚠️ **Action Required - Verify ROI extraction version**  
**Next Steps**: Check which version was used, re-run if necessary
