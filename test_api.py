import requests
import json

# Test the API endpoints directly
base_url = 'http://localhost:8000'

print('Testing patient-002 data...')
print('=' * 50)

# Test each resource type
resource_types = ['Observation', 'Encounter', 'MedicationRequest', 'AllergyIntolerance', 'Immunization', 'Procedure']

for resource_type in resource_types:
    try:
        response = requests.get(f'{base_url}/{resource_type}?patient=patient-002')
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f'{resource_type}: {total} records found')
            if total > 0 and 'entry' in data:
                # Show first record structure
                first_record = data['entry'][0]['resource']
                if 'subject' in first_record:
                    print(f'  Subject reference: {first_record["subject"].get("reference", "N/A")}')
                elif 'patient' in first_record:
                    print(f'  Patient reference: {first_record["patient"].get("reference", "N/A")}')
        else:
            print(f'{resource_type}: API error {response.status_code}')
    except Exception as e:
        print(f'{resource_type}: Error - {str(e)}')
    print()

# Also test without patient filter to see all data
print('\nTesting all data (no patient filter)...')
print('=' * 50)

for resource_type in resource_types:
    try:
        response = requests.get(f'{base_url}/{resource_type}')
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f'{resource_type}: {total} total records')
            if total > 0 and 'entry' in data:
                # Show first record structure
                first_record = data['entry'][0]['resource']
                if 'subject' in first_record:
                    print(f'  First record subject: {first_record["subject"].get("reference", "N/A")}')
                elif 'patient' in first_record:
                    print(f'  First record patient: {first_record["patient"].get("reference", "N/A")}')
        else:
            print(f'{resource_type}: API error {response.status_code}')
    except Exception as e:
        print(f'{resource_type}: Error - {str(e)}')
    print()
