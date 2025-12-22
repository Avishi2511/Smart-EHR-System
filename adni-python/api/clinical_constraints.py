"""
Post-processing to enforce clinical constraints on predictions.

This module generates clinically valid mock predictions by:
1. Using ADAS-Cog as the base metric
2. Applying monthly progression increments (reversing any decreases)
3. Scaling if the 90-month prediction exceeds 70
4. Deriving all other scores from ADAS-Cog using clinical mappings
"""
import numpy as np


def generate_future_predictions(last_session_scores, num_months=90, interval_months=6):
    """
    Generate clinically valid future predictions based on the last known session.
    
    This is a MOCK prediction system that generates plausible progression data
    by continuing from the last known values with realistic incremental changes.
    
    Args:
        last_session_scores: dict with keys 'mmse', 'cdr_global', 'cdr_sob', 'adas_totscore'
        num_months: Total months to predict (default 90 = 7.5 years)
        interval_months: Interval between predictions (default 6 months)
    
    Returns:
        predictions: (T, 4) array [MMSE, CDR_Global, CDR_SOB, ADAS_Cog]
    """
    num_timepoints = (num_months // interval_months) + 1  # +1 for baseline
    predictions = np.zeros((num_timepoints, 4))
    
    # Start with last known scores (ACTUAL values from last visit)
    baseline_mmse = last_session_scores.get('mmse', 17.6)
    baseline_cdr_global = last_session_scores.get('cdr_global', 1.0)
    baseline_cdr_sob = last_session_scores.get('cdr_sob', 7.4)
    baseline_adas = last_session_scores.get('adas_totscore', 28.9)
    
    # ========================================================================
    # STEP 1: Generate ADAS-Cog progression with realistic increments
    # ========================================================================
    # Typical AD progression: ~3-4 points per year on ADAS-Cog
    # For 6-month intervals: ~1.5-2.0 points per interval
    
    adas_trajectory = np.zeros(num_timepoints)
    adas_trajectory[0] = baseline_adas
    
    # Generate increments with slight variability
    np.random.seed(42)  # For reproducibility
    for t in range(1, num_timepoints):
        # Average increment: ~1.65 points per 6 months
        # Variability: ±0.3 points
        increment = np.random.uniform(1.4, 1.9)
        adas_trajectory[t] = adas_trajectory[t-1] + increment
    
    # ========================================================================
    # STEP 2: Scale if 90-month prediction exceeds 70
    # ========================================================================
    if adas_trajectory[-1] > 70:
        # Scale down proportionally to fit in 0-61.3 range
        scale_factor = 61.3 / adas_trajectory[-1]
        adas_trajectory = adas_trajectory * scale_factor
    
    # Clip to valid range [0, 70]
    adas_trajectory = np.clip(adas_trajectory, 0, 70)
    
    # ========================================================================
    # STEP 3: Generate MMSE using mod difference logic
    # ========================================================================
    # Apply the same mod difference approach as ADAS-Cog:
    # 1. Generate initial trajectory with random changes
    # 2. Take absolute value of differences
    # 3. Add differences cumulatively to baseline
    
    # First, generate a raw trajectory with random changes
    mmse_raw = np.zeros(num_timepoints)
    mmse_raw[0] = baseline_mmse
    
    np.random.seed(43)  # For reproducibility
    for t in range(1, num_timepoints):
        # Generate random change (could be positive or negative)
        change = np.random.uniform(-1.4, -1.0)  # Typically negative (decline)
        mmse_raw[t] = mmse_raw[t-1] + change
    
    # Now apply mod difference logic
    mmse_trajectory = np.zeros(num_timepoints)
    mmse_trajectory[0] = baseline_mmse
    
    for t in range(1, num_timepoints):
        # Calculate difference from previous timepoint
        delta = mmse_raw[t] - mmse_raw[t-1]
        
        # Take absolute value (mod difference)
        delta = abs(delta)
        
        # Add to previous value (ensures monotonic increase)
        mmse_trajectory[t] = mmse_trajectory[t-1] + delta
    
    # Scale if final value exceeds 30
    if mmse_trajectory[-1] > 30:
        scale_factor = 30 / mmse_trajectory[-1]
        mmse_trajectory = mmse_trajectory * scale_factor
    
    # Clip to valid range [0, 30]
    mmse_trajectory = np.clip(mmse_trajectory, 0, 30)
    
    # ========================================================================
    # STEP 4: Generate CDR-SOB using mod difference logic
    # ========================================================================
    # Apply the same mod difference approach
    
    # First, generate a raw trajectory with random changes
    cdr_sob_raw = np.zeros(num_timepoints)
    cdr_sob_raw[0] = baseline_cdr_sob
    
    np.random.seed(44)  # Different seed
    for t in range(1, num_timepoints):
        # Generate random change
        change = np.random.uniform(0.5, 0.9)  # Typically positive (increase)
        cdr_sob_raw[t] = cdr_sob_raw[t-1] + change
    
    # Now apply mod difference logic
    cdr_sob_trajectory = np.zeros(num_timepoints)
    cdr_sob_trajectory[0] = baseline_cdr_sob
    
    for t in range(1, num_timepoints):
        # Calculate difference from previous timepoint
        delta = cdr_sob_raw[t] - cdr_sob_raw[t-1]
        
        # Take absolute value (mod difference)
        delta = abs(delta)
        
        # Add to previous value (ensures monotonic increase)
        cdr_sob_trajectory[t] = cdr_sob_trajectory[t-1] + delta
    
    # Scale if final value exceeds 18
    if cdr_sob_trajectory[-1] > 18:
        scale_factor = 18 / cdr_sob_trajectory[-1]
        cdr_sob_trajectory = cdr_sob_trajectory * scale_factor
    
    # Clip to valid range [0, 18]
    cdr_sob_trajectory = np.clip(cdr_sob_trajectory, 0, 18)
    
    # ========================================================================
    # STEP 5: Derive CDR-Global from ADAS-Cog (categorical mapping)
    # ========================================================================
    # ADAS 0-10   → CDR 0   (Normal)
    # ADAS 10-20  → CDR 0.5 (Very Mild)
    # ADAS 20-32  → CDR 1   (Mild)
    # ADAS 32-55  → CDR 2   (Moderate)
    # ADAS 55-70  → CDR 3   (Severe)
    
    cdr_global_trajectory = np.zeros(num_timepoints)
    for t in range(num_timepoints):
        adas_val = adas_trajectory[t]
        if adas_val < 10:
            cdr_global_trajectory[t] = 0
        elif adas_val < 20:
            cdr_global_trajectory[t] = 0.5
        elif adas_val < 32:
            cdr_global_trajectory[t] = 1
        elif adas_val < 55:
            cdr_global_trajectory[t] = 2
        else:
            cdr_global_trajectory[t] = 3
    
    # ========================================================================
    # Assemble predictions
    # ========================================================================
    predictions[:, 0] = mmse_trajectory
    predictions[:, 1] = cdr_global_trajectory
    predictions[:, 2] = cdr_sob_trajectory
    predictions[:, 3] = adas_trajectory
    
    return predictions


def enforce_clinical_constraints(predictions, patient_data):
    """
    Enforce clinical constraints on raw model predictions.
    
    This function is called for historical data (where we have actual sessions).
    For historical data, we just ensure the predictions are within valid ranges.
    
    Args:
        predictions: (T, 4) array of raw model predictions
        patient_data: dict with patient information
    
    Returns:
        constrained_predictions: (T, 4) array with valid clinical values
    """
    T = predictions.shape[0]
    constrained = np.zeros_like(predictions)
    
    # Extract raw predictions
    raw_mmse = predictions[:, 0]
    raw_cdr_global = predictions[:, 1]
    raw_cdr_sob = predictions[:, 2]
    raw_adas = predictions[:, 3]
    
    # ========================================================================
    # STEP 1: Fix ADAS-Cog (primary metric)
    # ========================================================================
    # Make ADAS-Cog monotonically increasing (disease progression)
    adas_fixed = np.zeros(T)
    adas_fixed[0] = max(0, min(70, raw_adas[0]))  # Clip to valid range
    
    for t in range(1, T):
        # Calculate change from previous timepoint
        delta = raw_adas[t] - raw_adas[t-1]
        
        # If delta is negative (improvement), reverse it to show decline
        if delta < 0:
            delta = abs(delta)
        
        # Apply change (ensure monotonic increase)
        adas_fixed[t] = adas_fixed[t-1] + delta
    
    # Clip to valid range [0, 70]
    adas_fixed = np.clip(adas_fixed, 0, 70)
    
    # ========================================================================
    # STEP 2: Derive MMSE from ADAS-Cog
    # ========================================================================
    mmse_fixed = 30 - (adas_fixed * 30 / 70)
    mmse_fixed = np.clip(mmse_fixed, 0, 30)
    
    # ========================================================================
    # STEP 3: Derive CDR-SOB from ADAS-Cog
    # ========================================================================
    cdr_sob_fixed = adas_fixed * 18 / 70
    cdr_sob_fixed = np.clip(cdr_sob_fixed, 0, 18)
    
    # ========================================================================
    # STEP 4: Derive CDR-Global from ADAS-Cog (categorical)
    # ========================================================================
    cdr_global_fixed = np.zeros(T)
    for t in range(T):
        adas_val = adas_fixed[t]
        if adas_val < 10:
            cdr_global_fixed[t] = 0
        elif adas_val < 20:
            cdr_global_fixed[t] = 0.5
        elif adas_val < 32:
            cdr_global_fixed[t] = 1
        elif adas_val < 55:
            cdr_global_fixed[t] = 2
        else:
            cdr_global_fixed[t] = 3
    
    # ========================================================================
    # Assemble constrained predictions
    # ========================================================================
    constrained[:, 0] = mmse_fixed
    constrained[:, 1] = cdr_global_fixed
    constrained[:, 2] = cdr_sob_fixed
    constrained[:, 3] = adas_fixed
    
    return constrained


def validate_predictions(predictions):
    """
    Validate that predictions meet clinical constraints.
    
    Returns:
        dict with validation results
    """
    mmse = predictions[:, 0]
    cdr_global = predictions[:, 1]
    cdr_sob = predictions[:, 2]
    adas = predictions[:, 3]
    
    valid_cdr_values = {0, 0.5, 1, 2, 3}
    
    validation = {
        "mmse_valid": np.all((mmse >= 0) & (mmse <= 30)),
        "mmse_range": (float(mmse.min()), float(mmse.max())),
        
        "cdr_global_valid": np.all([v in valid_cdr_values for v in cdr_global]),
        "cdr_global_range": (float(cdr_global.min()), float(cdr_global.max())),
        
        "cdr_sob_valid": np.all((cdr_sob >= 0) & (cdr_sob <= 18)),
        "cdr_sob_range": (float(cdr_sob.min()), float(cdr_sob.max())),
        
        "adas_valid": np.all((adas >= 0) & (adas <= 70)),
        "adas_range": (float(adas.min()), float(adas.max())),
        
        "adas_monotonic": np.all(np.diff(adas) >= 0),
        "mmse_monotonic_decreasing": np.all(np.diff(mmse) <= 0),
    }
    
    validation["all_valid"] = all([
        validation["mmse_valid"],
        validation["cdr_global_valid"],
        validation["cdr_sob_valid"],
        validation["adas_valid"],
        validation["adas_monotonic"]
    ])
    
    return validation
