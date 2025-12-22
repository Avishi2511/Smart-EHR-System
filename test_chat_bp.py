import requests
import json

# Test with blood pressure query
url = "http://localhost:8001/api/chat/query"
data = {
    "patient_id": "patient-002",
    "query": "What was the patient's blood pressure in the last 3 months?"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}\n")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Query successful!")
        print(f"\nQuery: {result['query']}")
        print(f"Query Type: {result['query_type']}")
        print(f"Data Count: {result['count']}")
        
        if result['time_period']:
            print(f"Time Period: Last {result['time_period']['amount']} {result['time_period']['unit']}(s)")
        
        if result['data']:
            print("\nResults:")
            for item in result['data']:
                print(f"  - {item.get('display', 'N/A')}: {item.get('value', 'N/A')} {item.get('unit', '')}")
                print(f"    Date: {item.get('date', 'N/A')}")
        else:
            print("\nNo data found for this query")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Exception: {e}")
