import requests
import json

# Test medications query
print("=" * 70)
print("TEST 1: Medications Query")
print("=" * 70)

url = "http://localhost:8001/api/chat/query"
data = {
    "patient_id": "patient-002",
    "query": "What medications is the patient taking?"
}

response = requests.post(url, json=data)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"✅ Query Type: {result['query_type']}")
    print(f"✅ Data Count: {result['count']}")
    
    if result['data']:
        print("\nMedications:")
        for item in result['data']:
            print(f"  - {item.get('medication', 'N/A')}")
            print(f"    Status: {item.get('status', 'N/A')}")
    else:
        print("\n⚠️  No medications found")
else:
    print(f"❌ Error: {response.text}")

# Test conditions query
print("\n" + "=" * 70)
print("TEST 2: Conditions/Diagnoses Query")
print("=" * 70)

data = {
    "patient_id": "patient-002",
    "query": "What are the patient's current diagnoses?"
}

response = requests.post(url, json=data)
print(f"\nStatus: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"✅ Query Type: {result['query_type']}")
    print(f"✅ Data Count: {result['count']}")
    
    if result['data']:
        print("\nConditions:")
        for item in result['data']:
            print(f"  - {item.get('condition', 'N/A')}")
            print(f"    Status: {item.get('status', 'N/A')}")
    else:
        print("\n⚠️  No conditions found")
else:
    print(f"❌ Error: {response.text}")

print("\n" + "=" * 70)
