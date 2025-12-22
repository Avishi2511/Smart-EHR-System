import requests

# Get all observations for patient-002
r = requests.get('http://localhost:8000/Observation?patient=patient-002')
data = r.json()
observations = data.get('entry', [])

print(f'Found {len(observations)} observations for patient-002')

# Delete each observation
deleted_count = 0
for obs in observations:
    obs_id = obs['resource']['id']
    delete_response = requests.delete(f'http://localhost:8000/Observation/{obs_id}')
    if delete_response.status_code in [200, 204]:
        deleted_count += 1
        print(f'Deleted observation {obs_id}')
    else:
        print(f'Failed to delete observation {obs_id}: {delete_response.status_code}')

print(f'\nDeleted {deleted_count} out of {len(observations)} observations')

# Also delete conditions
r = requests.get('http://localhost:8000/Condition?patient=patient-002')
data = r.json()
conditions = data.get('entry', [])

print(f'\nFound {len(conditions)} conditions for patient-002')

deleted_count = 0
for cond in conditions:
    cond_id = cond['resource']['id']
    delete_response = requests.delete(f'http://localhost:8000/Condition/{cond_id}')
    if delete_response.status_code in [200, 204]:
        deleted_count += 1
        print(f'Deleted condition {cond_id}')
    else:
        print(f'Failed to delete condition {cond_id}: {delete_response.status_code}')

print(f'\nDeleted {deleted_count} out of {len(conditions)} conditions')

# Also delete medication requests
r = requests.get('http://localhost:8000/MedicationRequest?patient=patient-002')
data = r.json()
meds = data.get('entry', [])

print(f'\nFound {len(meds)} medication requests for patient-002')

deleted_count = 0
for med in meds:
    med_id = med['resource']['id']
    delete_response = requests.delete(f'http://localhost:8000/MedicationRequest/{med_id}')
    if delete_response.status_code in [200, 204]:
        deleted_count += 1
        print(f'Deleted medication request {med_id}')
    else:
        print(f'Failed to delete medication request {med_id}: {delete_response.status_code}')

print(f'\nDeleted {deleted_count} out of {len(meds)} medication requests')
print('\n✅ All clinical data for patient-002 has been cleared!')
