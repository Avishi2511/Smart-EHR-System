import requests
import json
import time

BASE_URL = "http://localhost:8000"

# Missing sample data for patient-002
missing_observations = [
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
    }
]

missing_encounters = [
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

missing_medication_requests = [
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-002",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Metformin 500mg (Glycomet)"},
        "subject": {"reference": "Patient/patient-002"},
        "dosageInstruction": [{"text": "Take twice daily with meals"}]
    },
    {
        "resourceType": "MedicationRequest",
        "id": "med-req-007",
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {"text": "Glimepiride 2mg (Amaryl)"},
        "subject": {"reference": "Patient/patient-002"},
        "dosageInstruction": [{"text": "Take once daily before breakfast"}]
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
