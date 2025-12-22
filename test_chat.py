import requests
import json

# Test the chat query endpoint
url = "http://localhost:8001/api/chat/query"
data = {
    "patient_id": "patient-002",
    "query": "What was the patient's blood pressure in the last 3 months?"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nResponse Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
