# ADNI Pipeline Testing - Issue & Resolution

## Issue Identified

**Problem**: Future predictions show flat line (all same values)

**Root Cause**: Only 1 session was preprocessed, so the model has no historical trend to extrapolate from.

**Code Logic** (predict_progression.py, lines 357-366):
```python
if len(predictions) >= 2:
    # Calculate trend from last 2 visits
    trend = predictions[-1] - predictions[-2]
    future_pred = predictions[-1] + (trend * (months_ahead / 6))
else:
    # If only one visit, use last prediction (FLAT LINE!)
    future_pred = predictions[-1]
```

## Solution

**Preprocess ALL 5 sessions** for patient 033S0567:
- 20061205 ✅ (already done)
- 20070607 ⏳ (in progress)
- 20071127 ⏳ (in progress)
- 20080605 ⏳ (in progress)
- 20090615 ⏳ (in progress)

Once all sessions are preprocessed, the model will:
1. See the progression across 5 timepoints (2006-2009)
2. Calculate the trend from the last 2 visits
3. Extrapolate future predictions based on that trend
4. **Generate a proper progression curve** (not a flat line!)

## Expected Output After Fix

With 5 sessions, you'll get:

**Historical Predictions** (Model Validation):
- Session 1 (2006-12-05): Actual vs Predicted scores
- Session 2 (2007-06-07): Actual vs Predicted scores
- Session 3 (2007-11-27): Actual vs Predicted scores
- Session 4 (2008-06-05): Actual vs Predicted scores
- Session 5 (2009-06-15): Actual vs Predicted scores

**Future Predictions** (Progression Forecast):
- +6 months: Extrapolated scores
- +12 months: Extrapolated scores
- +18 months: Extrapolated scores
- +24 months: Extrapolated scores
- +36 months: Extrapolated scores

The trend will be calculated as:
```
trend = Session_5_prediction - Session_4_prediction
future_6mo = Session_5_prediction + (trend * 1)
future_12mo = Session_5_prediction + (trend * 2)
future_18mo = Session_5_prediction + (trend * 3)
...
```

This will create a **proper progression graph** showing disease trajectory!

## How to Use

1. Wait for all preprocessing to complete (~20-25 minutes total)
2. Run: `python api/predict_progression.py --patient_id 033S0567`
3. Check output JSON: `api/predictions/033S0567_predictions.json`
4. Plot the data to visualize progression

## Graph Data Structure

The JSON output will have:

```json
{
  "historical_sessions": [
    {
      "session_date": "20061205",
      "actual_scores": {"MMSE": 25.0, "CDR_Global": 1.0, ...},
      "predicted_scores": {"MMSE": 23.9, "CDR_Global": 0.73, ...}
    },
    // ... 4 more sessions
  ],
  "future_predictions": [
    {
      "months_from_last_visit": 6,
      "predicted_scores": {"MMSE": 22.5, "CDR_Global": 0.85, ...}
    },
    {
      "months_from_last_visit": 12,
      "predicted_scores": {"MMSE": 21.8, "CDR_Global": 0.95, ...}
    },
    // ... showing progression/decline
  ]
}
```

## Visualization Example

You can plot:
- **X-axis**: Time (session dates + future months)
- **Y-axis**: Cognitive scores (MMSE, CDR, ADAS)
- **Lines**: 
  - Actual scores (historical)
  - Predicted scores (historical + future)
  - Trend line showing disease progression

This will show the **Alzheimer's disease progression trajectory** over time!
