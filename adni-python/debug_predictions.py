"""
Test to see what the model actually predicts for MMSE
"""
import json

with open('api/predictions/033S0567_predictions.json', 'r') as f:
    results = json.load(f)

print("\nModel's raw predictions vs constrained predictions:")
print("="*80)

for session in results["historical_sessions"]:
    date = session["session_date"]
    actual_mmse = session["actual_scores"].get("MMSE")
    pred_mmse = session["predicted_scores"].get("MMSE")
    
    print(f"Session {date}: Actual={actual_mmse}, Predicted={pred_mmse:.1f}")

print("\nFuture predictions:")
for future in results["future_predictions"][:5]:  # First 5
    months = future["months_from_last_visit"]
    mmse = future["predicted_scores"]["MMSE"]
    adas = future["predicted_scores"]["ADAS_Cog"]
    print(f"+{months} months: MMSE={mmse:.1f}, ADAS={adas:.1f}")
