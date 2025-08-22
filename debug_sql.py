import sqlite3
import json

# Connect to the FHIR database
db_path = "fhir-server/fhir.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Debug: Testing SQL JSON queries for patient-002")
    print("=" * 60)
    
    # First, let's see what data exists
    print("1. All resources in database:")
    cursor.execute("SELECT resource_type, COUNT(*) FROM fhir_resources GROUP BY resource_type")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]} records")
    
    print("\n2. Sample data for each resource type:")
    
    # Check Observation data
    print("\nObservation records:")
    cursor.execute("SELECT id, json_extract(data, '$.subject.reference') as subject_ref FROM fhir_resources WHERE resource_type = 'Observation'")
    obs_rows = cursor.fetchall()
    for row in obs_rows:
        print(f"   ID: {row[0]}, Subject: {row[1]}")
    
    # Check Encounter data  
    print("\nEncounter records:")
    cursor.execute("SELECT id, json_extract(data, '$.subject.reference') as subject_ref FROM fhir_resources WHERE resource_type = 'Encounter'")
    enc_rows = cursor.fetchall()
    for row in enc_rows:
        print(f"   ID: {row[0]}, Subject: {row[1]}")
    
    # Check MedicationRequest data
    print("\nMedicationRequest records:")
    cursor.execute("SELECT id, json_extract(data, '$.subject.reference') as subject_ref FROM fhir_resources WHERE resource_type = 'MedicationRequest'")
    med_rows = cursor.fetchall()
    for row in med_rows:
        print(f"   ID: {row[0]}, Subject: {row[1]}")
    
    # Check Condition data (this one works)
    print("\nCondition records:")
    cursor.execute("SELECT id, json_extract(data, '$.subject.reference') as subject_ref FROM fhir_resources WHERE resource_type = 'Condition'")
    cond_rows = cursor.fetchall()
    for row in cond_rows:
        print(f"   ID: {row[0]}, Subject: {row[1]}")
    
    print("\n3. Testing patient search queries:")
    
    # Test the exact queries from CRUD
    test_queries = [
        ("Observation", "SELECT COUNT(*) FROM fhir_resources WHERE resource_type = 'Observation' AND (json_extract(data, '$.subject.reference') LIKE '%patient-002%' OR json_extract(data, '$.subject.reference') LIKE '%Patient/patient-002%')"),
        ("Encounter", "SELECT COUNT(*) FROM fhir_resources WHERE resource_type = 'Encounter' AND (json_extract(data, '$.subject.reference') LIKE '%patient-002%' OR json_extract(data, '$.subject.reference') LIKE '%Patient/patient-002%')"),
        ("MedicationRequest", "SELECT COUNT(*) FROM fhir_resources WHERE resource_type = 'MedicationRequest' AND (json_extract(data, '$.subject.reference') LIKE '%patient-002%' OR json_extract(data, '$.subject.reference') LIKE '%Patient/patient-002%')"),
        ("Condition", "SELECT COUNT(*) FROM fhir_resources WHERE resource_type = 'Condition' AND (json_extract(data, '$.subject.reference') LIKE '%patient-002%' OR json_extract(data, '$.subject.reference') LIKE '%Patient/patient-002%')")
    ]
    
    for resource_type, query in test_queries:
        cursor.execute(query)
        count = cursor.fetchone()[0]
        print(f"   {resource_type}: {count} records found")
    
    print("\n4. Raw JSON data for patient-002 records:")
    
    # Show actual JSON for debugging
    cursor.execute("SELECT resource_type, data FROM fhir_resources WHERE json_extract(data, '$.subject.reference') LIKE '%patient-002%' OR json_extract(data, '$.patient.reference') LIKE '%patient-002%'")
    patient_records = cursor.fetchall()
    
    for resource_type, data_json in patient_records:
        data = json.loads(data_json)
        print(f"\n{resource_type} - ID: {data.get('id', 'N/A')}")
        if 'subject' in data:
            print(f"   Subject reference: {data['subject'].get('reference', 'N/A')}")
        if 'patient' in data:
            print(f"   Patient reference: {data['patient'].get('reference', 'N/A')}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
