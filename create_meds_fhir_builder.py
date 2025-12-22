import sys
sys.path.insert(0, 'backend')

import requests
from app.services.fhir_resource_builder import fhir_resource_builder

FHIR_SERVER = "http://localhost:8000"
PATIENT_ID = "patient-002"

# Sample medications
medications = [
    {"medication_text": "Metformin 500mg", "dosage": "500mg twice daily"},
    {"medication_text": "Lisinopril 10mg", "dosage": "10mg once daily"},
    {"medication_text": "Atorvastatin 20mg", "dosage": "20mg at bedtime"},
    {"medication_text": "Aspirin 81mg", "dosage": "81mg once daily"}
]

print(f"Creating {len(medications)} medications for patient {PATIENT_ID}...")
print("=" * 60)

created = 0
for med in medications:
    # Use the FHIR resource builder
    med_request = fhir_resource_builder.build_medication_request(
        medication_text=med["medication_text"],
        patient_id=PATIENT_ID,
        dosage_instruction=med["dosage"],
        status="active"
    )
    
    try:
        response = requests.post(
            f"{FHIR_SERVER}/MedicationRequest",
            json=med_request
        )
        
        if response.status_code in [200, 201]:
            created += 1
            print(f"✓ Created: {med['medication_text']}")
        else:
            print(f"✗ Failed: {med['medication_text']}")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text[:300]}")
    except Exception as e:
        print(f"✗ Error: {med['medication_text']} - {e}")

print(f"\n{'='*60}")
print(f"Created: {created}/{len(medications)}")

# Verify
r = requests.get(f"{FHIR_SERVER}/MedicationRequest?patient={PATIENT_ID}")
if r.status_code == 200:
    total = len(r.json().get('entry', []))
    print(f"✅ Total medications in FHIR: {total}")
    
print("\n🎉 Done!")
