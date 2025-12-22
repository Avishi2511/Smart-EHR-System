import requests

# Test FHIR query with code filter
url = "http://localhost:8000/Observation"
params = {
    "patient": "patient-002",
    "code": "2160-0"  # Creatinine LOINC code
}

r = requests.get(url, params=params)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

data = r.json()
entries = data.get('entry', [])
print(f"\nObservations found: {len(entries)}")

if entries:
    for entry in entries:
        resource = entry['resource']
        print(f"\nObservation ID: {resource['id']}")
        print(f"Code: {resource['code']['coding'][0]}")
        print(f"Value: {resource.get('valueQuantity', {})}")
