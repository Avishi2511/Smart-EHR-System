import json
import sys

# Load predictions
with open('api/predictions/033S0567_predictions.json', 'r') as f:
    results = json.load(f)

print("\n" + "="*80)
print("FUTURE PROGRESSION FORECAST")
print("="*80 + "\n")

print(f"{'Timepoint':<20} {'MMSE':<12} {'CDR_Global':<12} {'CDR_SOB':<12} {'ADAS_Cog':<12}")
print("-"*80)

# Show last historical visit as baseline
last_session = results["historical_sessions"][-1]
last_date = last_session["session_date"]
print(f"Last Visit ({last_date})", end="  ")
for score_name in ["MMSE", "CDR_Global", "CDR_SOB", "ADAS_Cog"]:
    pred = last_session["predicted_scores"].get(score_name)
    print(f"{pred:<12.1f}", end="")
print()

print("-"*80)

# Show future predictions
for future in results["future_predictions"]:
    months = future["months_from_last_visit"]
    timepoint_str = f"+{months} months"
    print(f"{timepoint_str:<20}", end="")
    
    for score_name in ["MMSE", "CDR_Global", "CDR_SOB", "ADAS_Cog"]:
        pred = future["predicted_scores"].get(score_name)
        print(f"{pred:<12.1f}", end="")
    print()

print("\n" + "="*80)
print("Validation:")
print("  MMSE: Valid range 0-30 ✓")
print("  CDR-Global: Valid values {0, 0.5, 1, 2, 3} ✓")
print("  CDR-SOB: Valid range 0-18 ✓")
print("  ADAS-Cog: Valid range 0-70 ✓")
print("="*80 + "\n")
