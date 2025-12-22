import requests

# Check if there are observations for patient-002
r = requests.get('http://localhost:8000/Observation?patient=patient-002')
data = r.json()
entries = data.get('entry', [])

print(f'Total observations for patient-002: {len(entries)}')

if entries:
    print('\nFirst 5 observations:')
    for i, entry in enumerate(entries[:5]):
        resource = entry['resource']
        code_display = resource['code']['coding'][0]['display']
        loinc_code = resource['code']['coding'][0].get('code', 'N/A')
        value = resource.get('valueQuantity', {}).get('value', 'N/A')
        unit = resource.get('valueQuantity', {}).get('unit', '')
        date = resource.get('effectiveDateTime', 'N/A')
        print(f'{i+1}. {code_display} (LOINC: {loinc_code}): {value} {unit} on {date}')
else:
    print('\nNo observations found for patient-002!')
    print('You need to upload a document first to extract observations.')
