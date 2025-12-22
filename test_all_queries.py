import requests

url = "http://localhost:8001/api/chat/query"

# Test all query types
tests = [
    ("Medications", "What medications is the patient taking?"),
    ("Conditions", "What are the patient's diagnoses?"),
    ("Blood Pressure", "What was the patient's blood pressure in the last 3 months?"),
    ("Latest Glucose", "Show me the latest glucose readings"),
    ("Average Heart Rate", "What is the average heart rate over the past month?"),
]

print("="*70)
print("COMPREHENSIVE QUERY CHAT TEST")
print("="*70)

for test_name, query in tests:
    print(f"\n{'='*70}")
    print(f"TEST: {test_name}")
    print(f"Query: \"{query}\"")
    print("="*70)
    
    response = requests.post(url, json={
        "patient_id": "patient-002",
        "query": query
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Success: {result['success']}")
        print(f"✅ Query Type: {result['query_type']}")
        print(f"✅ Data Count: {result['count']}")
        
        if result['count'] > 0:
            print(f"\n📊 Sample Data (first 3 items):")
            for i, item in enumerate(result['data'][:3], 1):
                print(f"  {i}. {item}")
        else:
            print("\n⚠️  No data returned")
            if result.get('error'):
                print(f"   Error: {result['error']}")
    else:
        print(f"❌ Status: {response.status_code}")
        print(f"❌ Error: {response.text[:200]}")

print("\n" + "="*70)
print("✅ ALL TESTS COMPLETE!")
print("="*70)
