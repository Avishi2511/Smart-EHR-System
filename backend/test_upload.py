import requests

files = {'file': ('test.txt', 'Blood Pressure: 140/90 mmHg\nGlucose: 120 mg/dL', 'text/plain')}
data = {'patient_id': 'patient-002', 'category': 'lab_report'}
headers = {'Origin': 'http://localhost:5173'}

r = requests.post('http://localhost:8001/api/files/upload', files=files, data=data, headers=headers)

print(f'Status: {r.status_code}')
print(f'CORS Header: {r.headers.get("access-control-allow-origin", "NOT PRESENT")}')
print(f'Response: {r.text[:1000]}')
