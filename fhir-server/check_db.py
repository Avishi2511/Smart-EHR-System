import sqlite3
import json

# Connect to database
conn = sqlite3.connect('fhir.db')
cursor = conn.cursor()

# Get all resources
cursor.execute("SELECT resource_type, id, data FROM fhir_resources WHERE resource_type='Patient' LIMIT 10")
patients = cursor.fetchall()

print(f"Found {len(patients)} patients in database:\n")
for resource_type, patient_id, data in patients:
    patient_data = json.loads(data)
    name = patient_data.get('name', [{}])[0]
    given = ' '.join(name.get('given', []))
    family = name.get('family', '')
    print(f"  ID: {patient_id}")
    print(f"  Name: {given} {family}")
    print()

conn.close()
