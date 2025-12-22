import requests
from datetime import datetime, timedelta

FHIR_SERVER = "http://localhost:8000"
PATIENT_ID = "patient-002"

# Sample Medications - simpler format
medications_data = [
    {"medication": "Metformin 500mg", "status": "active"},
    {"medication": "Lisinopril 10mg", "status": "active"},
    {"medication": "Atorvastatin 20mg", "status": "active"},
    {"medication": "Aspirin 81mg", "status": "active"}
]

print(f"Creating {len(medications_data)} medications for patient {PATIENT_ID}...")
print("=" * 60)

created = 0
for med_data in medications_data:
    medication_request = {
        "resourceType": "MedicationRequest",
        "status": med_data["status"],
        "intent": "order",
        "medicationCodeableConcept": {
            "text": med_data["medication"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}"
        },
        "authoredOn": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{FHIR_SERVER}/MedicationRequest",
            json=medication_request
        )
        
        if response.status_code in [200, 201]:
            created += 1
            print(f"✓ Created: {med_data['medication']}")
        else:
            print(f"✗ Failed: {med_data['medication']} - Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except Exception as e:
        print(f"✗ Error: {med_data['medication']} - {e}")

print(f"\n{'='*60}")
print(f"Created: {created}/{len(medications_data)}")

# Verify
r = requests.get(f"{FHIR_SERVER}/MedicationRequest?patient={PATIENT_ID}")
if r.status_code == 200:
    total = len(r.json().get('entry', []))
    print(f"✅ Total medications in FHIR: {total}")
