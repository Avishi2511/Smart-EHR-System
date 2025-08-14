import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

# Sample patient data
sample_patients = [
    {
        "resourceType": "Patient",
        "id": "patient-001",
        "name": [{"given": ["John"], "family": "Doe"}],
        "gender": "male",
        "birthDate": "1980-01-15",
        "address": [{"city": "New York", "state": "NY", "postalCode": "10001"}],
        "telecom": [{"system": "phone", "value": "+1-555-0123"}]
    },
    {
        "resourceType": "Patient", 
        "id": "patient-002",
        "name": [{"given": ["Jane"], "family": "Smith"}],
        "gender": "female",
        "birthDate": "1992-05-20",
        "address": [{"city": "Los Angeles", "state": "CA", "postalCode": "90210"}],
        "telecom": [{"system": "email", "value": "jane.smith@example.com"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-003", 
        "name": [{"given": ["Robert"], "family": "Johnson"}],
        "gender": "male",
        "birthDate": "1975-11-30",
        "address": [{"city": "Chicago", "state": "IL", "postalCode": "60601"}],
        "telecom": [{"system": "phone", "value": "+1-555-0456"}]
    }
]

# Sample observations
sample_observations = [
    {
        "resourceType": "Observation",
        "id": "obs-001",
        "status": "final",
        "code": {"text": "Blood Pressure"},
        "subject": {"reference": "Patient/patient-001"},
        "valueQuantity": {"value": 120, "unit": "mmHg"},
        "effectiveDateTime": "2024-01-01T10:00:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-002", 
        "status": "final",
        "code": {"text": "Heart Rate"},
        "subject": {"reference": "Patient/patient-002"},
        "valueQuantity": {"value": 72, "unit": "bpm"},
        "effectiveDateTime": "2024-01-01T10:00:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-003",
        "status": "final", 
        "code": {"text": "Body Temperature"},
        "subject": {"reference": "Patient/patient-001"},
        "valueQuantity": {"value": 98.6, "unit": "F"},
        "effectiveDateTime": "2024-01-02T09:30:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-004",
        "status": "final",
        "code": {"text": "Weight"},
        "subject": {"reference": "Patient/patient-003"},
        "valueQuantity": {"value": 180, "unit": "lbs"},
        "effectiveDateTime": "2024-01-03T14:15:00Z"
    }
]

# Sample conditions
sample_conditions = [
    {
        "resourceType": "Condition",
        "id": "condition-001",
        "code": {"text": "Hypertension"},
        "subject": {"reference": "Patient/patient-001"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2020-01-01"
    },
    {
        "resourceType": "Condition",
        "id": "condition-002",
        "code": {"text": "Type 2 Diabetes"},
        "subject": {"reference": "Patient/patient-002"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2019-06-15"
    }
]

# Sample encounters
sample_encounters = [
    {
        "resourceType": "Encounter",
        "id": "encounter-001",
        "status": "finished",
        "class": {"code": "outpatient"},
        "subject": {"reference": "Patient/patient-001"},
        "period": {
            "start": "2024-01-01T10:00:00Z",
            "end": "2024-01-01T11:00:00Z"
        }
    },
    {
        "resourceType": "Encounter",
        "id": "encounter-002",
        "status": "finished",
        "class": {"code": "outpatient"},
        "subject": {"reference": "Patient/patient-002"},
        "period": {
            "start": "2024-01-02T14:00:00Z",
            "end": "2024-01-02T15:30:00Z"
        }
    }
]

# Sample medication requests
sample_medication_requests = [
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-001",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Lisinopril 10mg"},
        "subject": {"reference": "Patient/patient-001"},
        "dosageInstruction": [{"text": "Take once daily"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-002",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Metformin 500mg"},
        "subject": {"reference": "Patient/patient-002"},
        "dosageInstruction": [{"text": "Take twice daily with meals"}]
    }
]

# Sample practitioners
sample_practitioners = [
    {
        "resourceType": "Practitioner",
        "id": "practitioner-001",
        "name": [{"given": ["Sarah"], "family": "Wilson", "prefix": ["Dr."]}],
        "gender": "female",
        "qualification": [
            {
                "code": {"text": "MD - Internal Medicine"},
                "issuer": {"display": "American Board of Internal Medicine"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+1-555-1001"},
            {"system": "email", "value": "sarah.wilson@hospital.com"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-002",
        "name": [{"given": ["Michael"], "family": "Chen", "prefix": ["Dr."]}],
        "gender": "male",
        "qualification": [
            {
                "code": {"text": "MD - Cardiology"},
                "issuer": {"display": "American Board of Cardiology"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+1-555-1002"},
            {"system": "email", "value": "michael.chen@hospital.com"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-003",
        "name": [{"given": ["Emily"], "family": "Rodriguez", "prefix": ["Dr."]}],
        "gender": "female",
        "qualification": [
            {
                "code": {"text": "MD - Family Medicine"},
                "issuer": {"display": "American Board of Family Medicine"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+1-555-1003"},
            {"system": "email", "value": "emily.rodriguez@hospital.com"}
        ]
    }
]

def check_server_health():
    """Check if the FHIR server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def load_resources(resource_type, resources):
    """Load a list of resources of a specific type"""
    print(f"\nLoading {len(resources)} {resource_type} resources...")
    
    for resource in resources:
        try:
            response = requests.post(
                f"{BASE_URL}/{resource_type}",
                json=resource,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Loaded {resource_type} {resource['id']}")
            else:
                print(f"✗ Failed to load {resource_type} {resource['id']}: {response.status_code}")
                print(f"  Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ Network error loading {resource_type} {resource['id']}: {str(e)}")
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)

def verify_data():
    """Verify that data was loaded correctly"""
    print("\nVerifying loaded data...")
    
    try:
        # Check patients
        response = requests.get(f"{BASE_URL}/Patient")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} patients")
        
        # Check practitioners
        response = requests.get(f"{BASE_URL}/Practitioner")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} practitioners")
        
        # Check observations
        response = requests.get(f"{BASE_URL}/Observation")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} observations")
            
        # Check conditions
        response = requests.get(f"{BASE_URL}/Condition")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found {data.get('total', 0)} conditions")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error verifying data: {str(e)}")

def main():
    print("FHIR Server Sample Data Loader")
    print("=" * 40)
    
    # Check if server is running
    print("Checking server health...")
    if not check_server_health():
        print("✗ FHIR server is not running or not accessible at", BASE_URL)
        print("Please start the server first with: python -m app.main")
        sys.exit(1)
    
    print("✓ FHIR server is running")
    
    # Load sample data
    load_resources("Patient", sample_patients)
    load_resources("Practitioner", sample_practitioners)
    load_resources("Observation", sample_observations)
    load_resources("Condition", sample_conditions)
    load_resources("Encounter", sample_encounters)
    load_resources("MedicationRequest", sample_medication_requests)
    
    # Verify data was loaded
    verify_data()
    
    print("\n" + "=" * 40)
    print("Sample data loading completed!")
    print(f"You can now access the FHIR server at: {BASE_URL}")
    print(f"API documentation available at: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
