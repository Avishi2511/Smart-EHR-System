import requests

# Check observations
r = requests.get('http://localhost:8000/Observation?patient=patient-002')
data = r.json()
entries = data.get('entry', [])

print(f'Total observations in FHIR server: {len(entries)}')
print()

if entries:
    print('Observations found:')
    for i, entry in enumerate(entries[:15]):
        resource = entry['resource']
        code_display = resource['code']['coding'][0]['display']
        value = resource.get('valueQuantity', {}).get('value', 'N/A')
        unit = resource.get('valueQuantity', {}).get('unit', '')
        print(f'{i+1}. {code_display}: {value} {unit}')
else:
    print('No observations found!')
    print('\nChecking if file was processed...')
    
    # Check backend logs
    import sys
    sys.path.insert(0, 'backend')
    from app.database import SessionLocal
    from app.models.sql_models import File
    
    db = SessionLocal()
    files = db.query(File).order_by(File.uploaded_at.desc()).limit(3).all()
    
    print(f'\nRecent files uploaded:')
    for f in files:
        print(f'- {f.filename}: Processed={f.processed}, Error={f.processing_error}')
    
    db.close()
