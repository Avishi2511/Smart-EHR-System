# Selected Test Patients with Complete Data

## Summary

From the ADNI dataset, I've identified **64 patients** with complete ROI features (MRI + PET preprocessed data).

Of these:
- **18 patients** have 3+ visits
- **34 patients** have 2+ visits

---

## Top Patients for Testing (Ranked by Number of Visits)

### Patients with 5 Visits (Best for Testing)

1. **033S0567**
   - Sessions: 20061205, 20070607, 20071127, 20080605, 20090615
   - Master ID: 033_S_0567
   - Gender: Male

2. **033S0906**
   - Sessions: 20070426, 20071001, 20080409, 20081008, 20091002
   - Master ID: 033_S_0906
   - Gender: Female

3. **021S0141**
   - Sessions: 20060808, 20070222, 20070806, 20080229, 20090224
   - Master ID: 021_S_0141
   - Gender: Male

---

### Patients with 4 Visits

4. **021S0231**
   - Sessions: 20060912, 20070321, 20070919, 20080904
   - Master ID: 021_S_0231
   - Gender: Male

5. **033S0511**
   - Sessions: 20061206, 20070606, 20071130, 20080604
   - Master ID: 033_S_0511
   - Gender: Male

6. **021S0626**
   - Sessions: 20070215, 20070807, 20080212, 20080827
   - Master ID: 021_S_0626
   - Gender: Male

7. **021S0424**
   - Sessions: 20061110, 20071113, 20080513, 20090512
   - Master ID: 021_S_0424
   - Gender: Male

---

### Patients with 3 Visits

8. **013S1205**
   - Sessions: 20070724, 20080124, 20090316
   - Master ID: 013_S_1205
   - Gender: Male

9. **021S0343**
   - Sessions: 20061025, 20070424, 20080429
   - Master ID: 021_S_0343
   - Gender: Male

10. **021S1109**
    - Sessions: 20070710, 20080110, 20080702
    - Master ID: 021_S_1109
    - Gender: Female

11. **033S0741**
    - Sessions: 20070810, 20080813, 20090814
    - Master ID: 033_S_0741
    - Gender: Female

12. **033S0889**
    - Sessions: 20070425, 20071001, 20081007
    - Master ID: 033_S_0889
    - Gender: Female

13. **033S0513**
    - Sessions: 20070531, 20071128, 20090602
    - Master ID: 033_S_0513
    - Gender: Male

14. **033S0723**
    - Sessions: 20070808, 20080220, 20090814
    - Master ID: 033_S_0723
    - Gender: Male

15. **137S0686**
    - Sessions: 20070212, 20080821, 20090729
    - Master ID: 137_S_0686
    - Gender: Male

16. **131S0497**
    - Sessions: 20070110, 20070619, 20080717
    - Master ID: 131_S_0497
    - Gender: Male

17. **137S0283**
    - Sessions: 20061030, 20080414, 20090423
    - Master ID: 137_S_0283
    - Gender: Male

18. **137S0481**
    - Sessions: 20061207, 20070524, 20071205
    - Master ID: 137_S_0481
    - Gender: Male

---

## Recommended Patients for Testing

### Top 5 for Comprehensive Testing:

1. **033S0567** (5 visits) - Best longitudinal data
2. **033S0906** (5 visits) - Female patient
3. **021S0141** (5 visits) - Multiple years of follow-up
4. **021S0231** (4 visits) - Good temporal coverage
5. **033S0511** (4 visits) - Consistent follow-up

---

## Data Availability

All these patients have:
- ✅ **Preprocessed MRI** (T1-weighted, brain extracted)
- ✅ **Preprocessed PET** (FDG-PET, SUVR normalized)
- ✅ **ROI Features** (93 MRI + 93 PET = 186 features)
- ✅ **Multiple visits** (longitudinal data for progression modeling)

---

## Note on Clinical Data

The clinical scores (MMSE, CDR, ADAS) appear to be in the master dataset but may need to be matched using the normalized subject IDs:
- ROI format: `033S0567`
- Master format: `033_S_0567`

The session tokens are dates in format `YYYYMMDD` (e.g., `20070426`).

---

## Next Steps

To use these patients for testing:

1. Extract their raw MRI/PET scans from `outputs/raw_nifti/`
2. Their ROI features are already in `outputs/roi_features.csv`
3. Clinical data can be extracted from `outputs/master_with_roi_features.csv` by matching subject IDs

---

**Total Patients Available**: 64  
**Patients with 3+ Visits**: 18  
**Patients with 5 Visits**: 3  
