import requests
from datetime import datetime, timedelta
import random

FHIR_SERVER = "http://localhost:8000"
PATIENT_ID = "patient-002"

# Sample observations with LOINC codes
observations_data = [
    # Blood Pressure (last 3 months)
    {"code": "8480-6", "display": "Systolic blood pressure", "value": 140, "unit": "mmHg", "days_ago": 5},
    {"code": "8462-4", "display": "Diastolic blood pressure", "value": 90, "unit": "mmHg", "days_ago": 5},
    {"code": "8480-6", "display": "Systolic blood pressure", "value": 135, "unit": "mmHg", "days_ago": 15},
    {"code": "8462-4", "display": "Diastolic blood pressure", "value": 85, "unit": "mmHg", "days_ago": 15},
    {"code": "8480-6", "display": "Systolic blood pressure", "value": 138, "unit": "mmHg", "days_ago": 30},
    {"code": "8462-4", "display": "Diastolic blood pressure", "value": 88, "unit": "mmHg", "days_ago": 30},
    {"code": "8480-6", "display": "Systolic blood pressure", "value": 142, "unit": "mmHg", "days_ago": 60},
    {"code": "8462-4", "display": "Diastolic blood pressure", "value": 92, "unit": "mmHg", "days_ago": 60},
    
    # Glucose (last 6 months)
    {"code": "2339-0", "display": "Glucose", "value": 110, "unit": "mg/dL", "days_ago": 7},
    {"code": "2339-0", "display": "Glucose", "value": 105, "unit": "mg/dL", "days_ago": 20},
    {"code": "2339-0", "display": "Glucose", "value": 115, "unit": "mg/dL", "days_ago": 45},
    {"code": "2339-0", "display": "Glucose", "value": 108, "unit": "mg/dL", "days_ago": 90},
    {"code": "2339-0", "display": "Glucose", "value": 112, "unit": "mg/dL", "days_ago": 120},
    {"code": "2339-0", "display": "Glucose", "value": 118, "unit": "mg/dL", "days_ago": 150},
    
    # Heart Rate (last 2 months)
    {"code": "8867-4", "display": "Heart rate", "value": 75, "unit": "beats/min", "days_ago": 3},
    {"code": "8867-4", "display": "Heart rate", "value": 72, "unit": "beats/min", "days_ago": 10},
    {"code": "8867-4", "display": "Heart rate", "value": 78, "unit": "beats/min", "days_ago": 25},
    {"code": "8867-4", "display": "Heart rate", "value": 74, "unit": "beats/min", "days_ago": 40},
    {"code": "8867-4", "display": "Heart rate", "value": 76, "unit": "beats/min", "days_ago": 55},
    
    # Body Temperature
    {"code": "8310-5", "display": "Body temperature", "value": 98.6, "unit": "°F", "days_ago": 5},
    {"code": "8310-5", "display": "Body temperature", "value": 98.4, "unit": "°F", "days_ago": 30},
    
    # Body Weight (last year)
    {"code": "29463-7", "display": "Body weight", "value": 75.5, "unit": "kg", "days_ago": 10},
    {"code": "29463-7", "display": "Body weight", "value": 76.0, "unit": "kg", "days_ago": 60},
    {"code": "29463-7", "display": "Body weight", "value": 76.8, "unit": "kg", "days_ago": 120},
    {"code": "29463-7", "display": "Body weight", "value": 77.2, "unit": "kg", "days_ago": 180},
    {"code": "29463-7", "display": "Body weight", "value": 77.5, "unit": "kg", "days_ago": 240},
    {"code": "29463-7", "display": "Body weight", "value": 78.0, "unit": "kg", "days_ago": 300},
    {"code": "29463-7", "display": "Body weight", "value": 78.5, "unit": "kg", "days_ago": 360},
    
    # Cholesterol
    {"code": "2093-3", "display": "Cholesterol total", "value": 195, "unit": "mg/dL", "days_ago": 30},
    {"code": "2085-9", "display": "HDL Cholesterol", "value": 45, "unit": "mg/dL", "days_ago": 30},
    {"code": "2089-1", "display": "LDL Cholesterol", "value": 125, "unit": "mg/dL", "days_ago": 30},
    
    # HbA1c
    {"code": "4548-4", "display": "Hemoglobin A1c", "value": 6.2, "unit": "%", "days_ago": 45},
    {"code": "4548-4", "display": "Hemoglobin A1c", "value": 6.1, "unit": "%", "days_ago": 135},
    
    # Hemoglobin
    {"code": "718-7", "display": "Hemoglobin", "value": 14.5, "unit": "g/dL", "days_ago": 30},
    
    # Oxygen Saturation
    {"code": "2708-6", "display": "Oxygen saturation", "value": 98, "unit": "%", "days_ago": 5},
    {"code": "2708-6", "display": "Oxygen saturation", "value": 97, "unit": "%", "days_ago": 30},
]

def create_observation(obs_data):
    """Create a FHIR Observation resource"""
    effective_date = (datetime.now() - timedelta(days=obs_data["days_ago"])).isoformat()
    
    observation = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": obs_data["code"],
                "display": obs_data["display"]
            }],
            "text": obs_data["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}"
        },
        "effectiveDateTime": effective_date,
        "valueQuantity": {
            "value": obs_data["value"],
            "unit": obs_data["unit"],
            "system": "http://unitsofmeasure.org"
        }
    }
    
    return observation

# Create all observations
print(f"Creating {len(observations_data)} observations for patient {PATIENT_ID}...")
created_count = 0
failed_count = 0

for obs_data in observations_data:
    observation = create_observation(obs_data)
    
    try:
        response = requests.post(
            f"{FHIR_SERVER}/Observation",
            json=observation
        )
        
        if response.status_code in [200, 201]:
            created_count += 1
            print(f"✓ Created: {obs_data['display']} ({obs_data['value']} {obs_data['unit']}) - {obs_data['days_ago']} days ago")
        else:
            failed_count += 1
            print(f"✗ Failed: {obs_data['display']} - Status: {response.status_code}")
    except Exception as e:
        failed_count += 1
        print(f"✗ Error creating {obs_data['display']}: {e}")

print(f"\n{'='*60}")
print(f"Summary:")
print(f"  Created: {created_count}")
print(f"  Failed: {failed_count}")
print(f"  Total: {len(observations_data)}")
print(f"{'='*60}")

# Verify observations were created
verify_response = requests.get(f"{FHIR_SERVER}/Observation?patient={PATIENT_ID}")
if verify_response.status_code == 200:
    total_obs = len(verify_response.json().get("entry", []))
    print(f"\n✅ Verification: {total_obs} total observations now exist for patient {PATIENT_ID}")
else:
    print(f"\n⚠️  Could not verify observations")

print("\n🎉 Sample data creation complete!")
print("\nYou can now test these queries:")
print("  - 'What was the patient's blood pressure in the last 3 months?'")
print("  - 'Show me the latest glucose readings'")
print("  - 'What is the average heart rate over the past month?'")
print("  - 'Show the patient's weight trend over the last year'")
print("  - 'What was the latest HbA1c?'")
