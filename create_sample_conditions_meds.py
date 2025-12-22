import requests
from datetime import datetime, timedelta

FHIR_SERVER = "http://localhost:8000"
PATIENT_ID = "patient-002"

# Sample Conditions (Diagnoses)
conditions_data = [
    {
        "code": "I10",
        "display": "Essential (primary) hypertension",
        "system": "http://hl7.org/fhir/sid/icd-10",
        "status": "active",
        "onset_days_ago": 365
    },
    {
        "code": "E11",
        "display": "Type 2 diabetes mellitus",
        "system": "http://hl7.org/fhir/sid/icd-10",
        "status": "active",
        "onset_days_ago": 730
    },
    {
        "code": "E78.5",
        "display": "Hyperlipidemia",
        "system": "http://hl7.org/fhir/sid/icd-10",
        "status": "active",
        "onset_days_ago": 500
    }
]

# Sample Medications
medications_data = [
    {
        "medication": "Metformin 500mg",
        "dosage": "500 mg twice daily",
        "status": "active",
        "authored_days_ago": 90
    },
    {
        "medication": "Lisinopril 10mg",
        "dosage": "10 mg once daily",
        "status": "active",
        "authored_days_ago": 120
    },
    {
        "medication": "Atorvastatin 20mg",
        "dosage": "20 mg once daily at bedtime",
        "status": "active",
        "authored_days_ago": 150
    },
    {
        "medication": "Aspirin 81mg",
        "dosage": "81 mg once daily",
        "status": "active",
        "authored_days_ago": 200
    }
]

def create_condition(cond_data):
    """Create a FHIR Condition resource"""
    onset_date = (datetime.now() - timedelta(days=cond_data["onset_days_ago"])).isoformat()
    
    condition = {
        "resourceType": "Condition",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": cond_data["status"]
            }]
        },
        "code": {
            "coding": [{
                "system": cond_data["system"],
                "code": cond_data["code"],
                "display": cond_data["display"]
            }],
            "text": cond_data["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}"
        },
        "onsetDateTime": onset_date
    }
    
    return condition

def create_medication_request(med_data):
    """Create a FHIR MedicationRequest resource"""
    authored_date = (datetime.now() - timedelta(days=med_data["authored_days_ago"])).isoformat()
    
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
        "authoredOn": authored_date,
        "dosageInstruction": [{
            "text": med_data["dosage"]
        }]
    }
    
    return medication_request

# Create Conditions
print(f"Creating {len(conditions_data)} conditions for patient {PATIENT_ID}...")
print("=" * 60)

created_conditions = 0
for cond_data in conditions_data:
    condition = create_condition(cond_data)
    
    try:
        response = requests.post(
            f"{FHIR_SERVER}/Condition",
            json=condition
        )
        
        if response.status_code in [200, 201]:
            created_conditions += 1
            print(f"✓ Created condition: {cond_data['display']}")
            print(f"  Status: {cond_data['status']}, Onset: {cond_data['onset_days_ago']} days ago")
        else:
            print(f"✗ Failed to create: {cond_data['display']} - Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error creating {cond_data['display']}: {e}")

print(f"\n{'='*60}")
print(f"Conditions Created: {created_conditions}/{len(conditions_data)}")
print(f"{'='*60}\n")

# Create Medications
print(f"Creating {len(medications_data)} medications for patient {PATIENT_ID}...")
print("=" * 60)

created_medications = 0
for med_data in medications_data:
    medication_request = create_medication_request(med_data)
    
    try:
        response = requests.post(
            f"{FHIR_SERVER}/MedicationRequest",
            json=medication_request
        )
        
        if response.status_code in [200, 201]:
            created_medications += 1
            print(f"✓ Created medication: {med_data['medication']}")
            print(f"  Dosage: {med_data['dosage']}")
            print(f"  Status: {med_data['status']}, Prescribed: {med_data['authored_days_ago']} days ago")
        else:
            print(f"✗ Failed to create: {med_data['medication']} - Status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error creating {med_data['medication']}: {e}")

print(f"\n{'='*60}")
print(f"Medications Created: {created_medications}/{len(medications_data)}")
print(f"{'='*60}\n")

# Verify
print("Verifying data...")
print("=" * 60)

# Check conditions
cond_response = requests.get(f"{FHIR_SERVER}/Condition?patient={PATIENT_ID}")
if cond_response.status_code == 200:
    total_cond = len(cond_response.json().get("entry", []))
    print(f"✅ Total conditions for {PATIENT_ID}: {total_cond}")
else:
    print(f"⚠️  Could not verify conditions")

# Check medications
med_response = requests.get(f"{FHIR_SERVER}/MedicationRequest?patient={PATIENT_ID}")
if med_response.status_code == 200:
    total_med = len(med_response.json().get("entry", []))
    print(f"✅ Total medications for {PATIENT_ID}: {total_med}")
else:
    print(f"⚠️  Could not verify medications")

print(f"{'='*60}\n")

print("🎉 Sample conditions and medications created!")
print("\nYou can now test these queries:")
print("  - 'What medications is the patient taking?'")
print("  - 'What are the patient's current diagnoses?'")
print("  - 'What conditions does the patient have?'")
print("  - 'Show me all active medications'")
