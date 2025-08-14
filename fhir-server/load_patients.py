import requests
import json

patients = [
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

print("Loading patients...")
for patient in patients:
    try:
        response = requests.post("http://localhost:8000/Patient", json=patient)
        print(f"Patient {patient['id']}: Status {response.status_code}")
        if response.status_code not in [200, 201]:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error loading {patient['id']}: {e}")

# Verify patients were loaded
response = requests.get("http://localhost:8000/Patient")
if response.status_code == 200:
    data = response.json()
    print(f"\nTotal patients in database: {data.get('total', 0)}")
else:
    print(f"Error checking patients: {response.status_code}")
