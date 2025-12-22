import requests
import json

url = "http://localhost:8001/api/chat/query"

# Test 1: Medications
print("="*70)
print("TEST 1: MEDICATIONS QUERY")
print("="*70)

response = requests.post(url, json={
    "patient_id": "patient-002",
    "query": "What medications is the patient taking?"
})

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Query Type: {result['query_type']}")
    print(f"Count: {result['count']}")
    print(f"\nFull Response:")
    print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.text}")

# Test 2: Conditions  
print("\n" + "="*70)
print("TEST 2: CONDITIONS QUERY")
print("="*70)

response = requests.post(url, json={
    "patient_id": "patient-002",
    "query": "What are the patient's diagnoses?"
})

print(f"Status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Success: {result['success']}")
    print(f"Query Type: {result['query_type']}")
    print(f"Count: {result['count']}")
    print(f"\nFull Response:")
    print(json.dumps(result, indent=2))
else:
    print(f"Error: {response.text}")
