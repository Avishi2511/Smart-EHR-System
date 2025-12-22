import requests

# Test conditions query
url = "http://localhost:8001/api/chat/query"
data = {
    "patient_id": "patient-002",
    "query": "What are the patient's diagnoses?"
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    result = response.json()
    print(f"✅ Success!")
    print(f"Query Type: {result['query_type']}")
    print(f"Data Count: {result['count']}\n")
    
    if result['data']:
        print("Conditions found:")
        for i, item in enumerate(result['data'], 1):
            print(f"{i}. {item.get('condition', 'N/A')}")
            print(f"   Status: {item.get('status', 'N/A')}")
            if item.get('onset'):
                print(f"   Onset: {item.get('onset')}")
    else:
        print("No conditions found")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
