import requests

# Check medications
print("Checking Medications...")
r = requests.get('http://localhost:8000/MedicationRequest?patient=patient-002')
meds = r.json().get('entry', [])
print(f"Total medications: {len(meds)}")
if meds:
    for i, entry in enumerate(meds[:5]):
        med = entry['resource']
        print(f"{i+1}. {med.get('medicationCodeableConcept', {}).get('text', 'N/A')}")
        print(f"   Status: {med.get('status', 'N/A')}")

print("\n" + "="*60 + "\n")

# Check conditions
print("Checking Conditions...")
r = requests.get('http://localhost:8000/Condition?patient=patient-002')
conds = r.json().get('entry', [])
print(f"Total conditions: {len(conds)}")
if conds:
    for i, entry in enumerate(conds[:5]):
        cond = entry['resource']
        print(f"{i+1}. {cond.get('code', {}).get('text', 'N/A')}")
        status_code = cond.get('clinicalStatus', {}).get('coding', [{}])[0].get('code', 'N/A')
        print(f"   Status: {status_code}")
