import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

# Sample patient data - Indian context
sample_patients = [
    {
        "resourceType": "Patient",
        "id": "patient-001",
        "name": [{"given": ["Rajesh"], "family": "Kumar"}],
        "gender": "male",
        "birthDate": "1985-03-15",
        "address": [{"city": "Mumbai", "state": "Maharashtra", "postalCode": "400001"}],
        "telecom": [{"system": "phone", "value": "+91-98765-43210"}]
    },
    {
        "resourceType": "Patient", 
        "id": "patient-002",
        "name": [{"given": ["Priya"], "family": "Sharma"}],
        "gender": "female",
        "birthDate": "1990-07-22",
        "address": [{"city": "Delhi", "state": "Delhi", "postalCode": "110001"}],
        "telecom": [{"system": "email", "value": "priya.sharma@gmail.com"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-003", 
        "name": [{"given": ["Arjun"], "family": "Patel"}],
        "gender": "male",
        "birthDate": "1978-12-08",
        "address": [{"city": "Bangalore", "state": "Karnataka", "postalCode": "560001"}],
        "telecom": [{"system": "phone", "value": "+91-99876-54321"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-004",
        "name": [{"given": ["Sneha"], "family": "Reddy"}],
        "gender": "female",
        "birthDate": "1987-09-14",
        "address": [{"city": "Hyderabad", "state": "Telangana", "postalCode": "500001"}],
        "telecom": [{"system": "phone", "value": "+91-98123-45678"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-005",
        "name": [{"given": ["Vikram"], "family": "Singh"}],
        "gender": "male",
        "birthDate": "1982-11-30",
        "address": [{"city": "Jaipur", "state": "Rajasthan", "postalCode": "302001"}],
        "telecom": [{"system": "email", "value": "vikram.singh@yahoo.in"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-006",
        "name": [{"given": ["Kavya"], "family": "Nair"}],
        "gender": "female",
        "birthDate": "1993-04-18",
        "address": [{"city": "Kochi", "state": "Kerala", "postalCode": "682001"}],
        "telecom": [{"system": "phone", "value": "+91-97654-32109"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-007",
        "name": [{"given": ["Amit"], "family": "Gupta"}],
        "gender": "male",
        "birthDate": "1975-06-25",
        "address": [{"city": "Pune", "state": "Maharashtra", "postalCode": "411001"}],
        "telecom": [{"system": "phone", "value": "+91-98234-56789"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-008",
        "name": [{"given": ["Meera"], "family": "Iyer"}],
        "gender": "female",
        "birthDate": "1988-01-12",
        "address": [{"city": "Chennai", "state": "Tamil Nadu", "postalCode": "600001"}],
        "telecom": [{"system": "email", "value": "meera.iyer@hotmail.com"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-009",
        "name": [{"given": ["Rohit"], "family": "Agarwal"}],
        "gender": "male",
        "birthDate": "1991-10-03",
        "address": [{"city": "Kolkata", "state": "West Bengal", "postalCode": "700001"}],
        "telecom": [{"system": "phone", "value": "+91-96543-21098"}]
    },
    {
        "resourceType": "Patient",
        "id": "patient-010",
        "name": [{"given": ["Ananya"], "family": "Joshi"}],
        "gender": "female",
        "birthDate": "1986-05-07",
        "address": [{"city": "Ahmedabad", "state": "Gujarat", "postalCode": "380001"}],
        "telecom": [{"system": "phone", "value": "+91-95432-10987"}]
    }
]

# Sample observations - Indian context with more comprehensive data
sample_observations = [
    {
        "resourceType": "Observation",
        "id": "obs-001",
        "status": "final",
        "code": {"text": "Blood Pressure"},
        "subject": {"reference": "Patient/patient-001"},
        "valueQuantity": {"value": 140, "unit": "mmHg"},
        "effectiveDateTime": "2024-01-15T10:00:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-002", 
        "status": "final",
        "code": {"text": "Blood Sugar (Fasting)"},
        "subject": {"reference": "Patient/patient-002"},
        "valueQuantity": {"value": 126, "unit": "mg/dL"},
        "effectiveDateTime": "2024-01-16T08:00:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-003",
        "status": "final", 
        "code": {"text": "HbA1c"},
        "subject": {"reference": "Patient/patient-002"},
        "valueQuantity": {"value": 7.2, "unit": "%"},
        "effectiveDateTime": "2024-01-16T08:30:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-004",
        "status": "final",
        "code": {"text": "Weight"},
        "subject": {"reference": "Patient/patient-003"},
        "valueQuantity": {"value": 75, "unit": "kg"},
        "effectiveDateTime": "2024-01-17T14:15:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-005",
        "status": "final",
        "code": {"text": "Vitamin D"},
        "subject": {"reference": "Patient/patient-004"},
        "valueQuantity": {"value": 18, "unit": "ng/mL"},
        "effectiveDateTime": "2024-01-18T11:00:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-006",
        "status": "final",
        "code": {"text": "Thyroid TSH"},
        "subject": {"reference": "Patient/patient-005"},
        "valueQuantity": {"value": 8.5, "unit": "mIU/L"},
        "effectiveDateTime": "2024-01-19T09:30:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-007",
        "status": "final",
        "code": {"text": "Hemoglobin"},
        "subject": {"reference": "Patient/patient-006"},
        "valueQuantity": {"value": 9.8, "unit": "g/dL"},
        "effectiveDateTime": "2024-01-20T10:45:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-008",
        "status": "final",
        "code": {"text": "Cholesterol (Total)"},
        "subject": {"reference": "Patient/patient-007"},
        "valueQuantity": {"value": 220, "unit": "mg/dL"},
        "effectiveDateTime": "2024-01-21T08:15:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-009",
        "status": "final",
        "code": {"text": "Blood Pressure"},
        "subject": {"reference": "Patient/patient-008"},
        "valueQuantity": {"value": 130, "unit": "mmHg"},
        "effectiveDateTime": "2024-01-22T11:30:00Z"
    },
    {
        "resourceType": "Observation",
        "id": "obs-010",
        "status": "final",
        "code": {"text": "BMI"},
        "subject": {"reference": "Patient/patient-009"},
        "valueQuantity": {"value": 28.5, "unit": "kg/m2"},
        "effectiveDateTime": "2024-01-23T14:00:00Z"
    }
]

# Sample conditions - Indian context with prevalent conditions
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
        "code": {"text": "Type 2 Diabetes Mellitus"},
        "subject": {"reference": "Patient/patient-002"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2019-06-15"
    },
    {
        "resourceType": "Condition",
        "id": "condition-003",
        "code": {"text": "Vitamin D Deficiency"},
        "subject": {"reference": "Patient/patient-004"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2023-03-10"
    },
    {
        "resourceType": "Condition",
        "id": "condition-004",
        "code": {"text": "Hypothyroidism"},
        "subject": {"reference": "Patient/patient-005"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2021-08-20"
    },
    {
        "resourceType": "Condition",
        "id": "condition-005",
        "code": {"text": "Iron Deficiency Anemia"},
        "subject": {"reference": "Patient/patient-006"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2022-11-05"
    },
    {
        "resourceType": "Condition",
        "id": "condition-006",
        "code": {"text": "Dyslipidemia"},
        "subject": {"reference": "Patient/patient-007"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2021-04-12"
    },
    {
        "resourceType": "Condition",
        "id": "condition-007",
        "code": {"text": "Obesity"},
        "subject": {"reference": "Patient/patient-009"},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2020-09-18"
    }
]

# Sample encounters
sample_encounters = [
    {
        "resourceType": "Encounter",
        "id": "encounter-001",
        "status": "finished",
        "class": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            }]
        }],
        "subject": {"reference": "Patient/patient-001"},
        "actualPeriod": {
            "start": "2024-01-01T10:00:00Z",
            "end": "2024-01-01T11:00:00Z"
        }
    },
    {
        "resourceType": "Encounter",
        "id": "encounter-002",
        "status": "finished",
        "class": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
                "display": "ambulatory"
            }]
        }],
        "subject": {"reference": "Patient/patient-002"},
        "actualPeriod": {
            "start": "2024-01-02T14:00:00Z",
            "end": "2024-01-02T15:30:00Z"
        }
    }
]

# Sample medication requests - Indian brands and context
sample_medication_requests = [
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-001",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Amlodipine 5mg (Amlong)"
            }
        },
        "subject": {"reference": "Patient/patient-001"},
        "dosageInstruction": [{"text": "Take once daily in the morning"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-002",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Metformin 500mg (Glycomet)"
            }
        },
        "subject": {"reference": "Patient/patient-002"},
        "dosageInstruction": [{"text": "Take twice daily with meals"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-003",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Vitamin D3 60000 IU (Calcirol)"
            }
        },
        "subject": {"reference": "Patient/patient-004"},
        "dosageInstruction": [{"text": "Take once weekly"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-004",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Levothyroxine 50mcg (Thyronorm)"
            }
        },
        "subject": {"reference": "Patient/patient-005"},
        "dosageInstruction": [{"text": "Take once daily on empty stomach"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-005",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Iron + Folic Acid (Fefol)"
            }
        },
        "subject": {"reference": "Patient/patient-006"},
        "dosageInstruction": [{"text": "Take once daily after meals"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-006",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Atorvastatin 20mg (Lipitor)"
            }
        },
        "subject": {"reference": "Patient/patient-007"},
        "dosageInstruction": [{"text": "Take once daily at bedtime"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-007",
        "status": "active",
        "intent": "order",
        "medication": {
            "concept": {
                "text": "Glimepiride 2mg (Amaryl)"
            }
        },
        "subject": {"reference": "Patient/patient-002"},
        "dosageInstruction": [{"text": "Take once daily before breakfast"}]
    }
]

# Sample practitioners - Indian context
sample_practitioners = [
    {
        "resourceType": "Practitioner",
        "id": "practitioner-001",
        "name": [{"given": ["Sunita"], "family": "Gupta", "prefix": ["Dr."]}],
        "gender": "female",
        "qualification": [
            {
                "code": {"text": "MBBS, MD - Internal Medicine"},
                "issuer": {"display": "Medical Council of India"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+91-98765-11001"},
            {"system": "email", "value": "dr.sunita.gupta@aiims.edu"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-002",
        "name": [{"given": ["Vikram"], "family": "Singh", "prefix": ["Dr."]}],
        "gender": "male",
        "qualification": [
            {
                "code": {"text": "MBBS, DM - Cardiology"},
                "issuer": {"display": "Medical Council of India"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+91-98765-11002"},
            {"system": "email", "value": "dr.vikram.singh@fortis.in"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-003",
        "name": [{"given": ["Meera"], "family": "Reddy", "prefix": ["Dr."]}],
        "gender": "female",
        "qualification": [
            {
                "code": {"text": "MBBS, MD - Family Medicine"},
                "issuer": {"display": "Medical Council of India"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+91-98765-11003"},
            {"system": "email", "value": "dr.meera.reddy@apollo.in"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-004",
        "name": [{"given": ["Rajesh"], "family": "Agarwal", "prefix": ["Dr."]}],
        "gender": "male",
        "qualification": [
            {
                "code": {"text": "MBBS, MS - Orthopedics"},
                "issuer": {"display": "Medical Council of India"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+91-98765-11004"},
            {"system": "email", "value": "dr.rajesh.agarwal@maxhealthcare.in"}
        ]
    },
    {
        "resourceType": "Practitioner",
        "id": "practitioner-005",
        "name": [{"given": ["Kavitha"], "family": "Nair", "prefix": ["Dr."]}],
        "gender": "female",
        "qualification": [
            {
                "code": {"text": "MBBS, MD - Pediatrics"},
                "issuer": {"display": "Medical Council of India"}
            }
        ],
        "telecom": [
            {"system": "phone", "value": "+91-98765-11005"},
            {"system": "email", "value": "dr.kavitha.nair@manipal.edu"}
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
