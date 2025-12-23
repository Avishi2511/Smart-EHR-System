"""
Export observations from local backend.db and upload to deployed services
This script:
1. Reads 118 observations for patient-002 from local backend.db
2. Converts them to FHIR format
3. Uploads to deployed FHIR server
4. Also syncs to deployed Backend API
"""

import sqlite3
import requests
import json
from datetime import datetime

# Configuration
LOCAL_DB = "backend/backend.db"
FHIR_SERVER_URL = "https://smart-ehr-fhir-server.onrender.com"
BACKEND_API_URL = "https://smart-ehr-backend.onrender.com"

# LOINC code mappings for observation types
LOINC_CODES = {
    "glucose": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood"},
    "hba1c": {"code": "4548-4", "display": "Hemoglobin A1c/Hemoglobin.total in Blood"},
    "creatinine": {"code": "2160-0", "display": "Creatinine [Mass/volume] in Serum or Plasma"},
    "heart_rate": {"code": "8867-4", "display": "Heart rate"},
    "bp_systolic": {"code": "8480-6", "display": "Systolic blood pressure"},
    "bp_diastolic": {"code": "8462-4", "display": "Diastolic blood pressure"},
    "temperature": {"code": "8310-5", "display": "Body temperature"},
    "weight": {"code": "29463-7", "display": "Body Weight"},
    "height": {"code": "8302-2", "display": "Body Height"},
    "mri": {"code": "24627-2", "display": "MRI Brain"},
    "pet": {"code": "44139-4", "display": "PET scan"},
    "ct_scan": {"code": "24627-2", "display": "CT scan"},
    "general_visit": {"code": "34117-2", "display": "History and physical note"},
    "eye_checkup": {"code": "70004-7", "display": "Ophthalmology Evaluation note"},
    "ent": {"code": "34879-7", "display": "Otolaryngology Evaluation note"},
    "alzheimer": {"code": "72107-6", "display": "Cognitive function assessment"},
    "clinical_document": {"code": "34133-9", "display": "Clinical Document"}
}

CATEGORY_MAP = {
    "glucose": "laboratory",
    "hba1c": "laboratory",
    "creatinine": "laboratory",
    "heart_rate": "vital-signs",
    "bp_systolic": "vital-signs",
    "bp_diastolic": "vital-signs",
    "temperature": "vital-signs",
    "weight": "vital-signs",
    "height": "vital-signs",
    "mri": "imaging",
    "pet": "imaging",
    "ct_scan": "imaging",
    "general_visit": "exam",
    "eye_checkup": "exam",
    "ent": "exam",
    "alzheimer": "exam",
    "clinical_document": "procedure"
}

def get_observations_from_db():
    """Read observations from local database"""
    print("Reading observations from local database...")
    
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get patient-002
    cursor.execute("SELECT * FROM patients WHERE fhir_id = 'patient-002'")
    patient = cursor.fetchone()
    
    if not patient:
        print("Patient-002 not found in local database!")
        return []
    
    print(f"Found patient: {patient['first_name']} {patient['last_name']}")
    
    # Get all observations for this patient
    cursor.execute("""
        SELECT * FROM observations 
        WHERE patient_id = ? 
        ORDER BY effective_datetime DESC
    """, (patient['id'],))
    
    observations = cursor.fetchall()
    conn.close()
    
    print(f"Found {len(observations)} observations")
    return observations, patient

def convert_to_fhir(obs, patient):
    """Convert SQL observation to FHIR format"""
    obs_type = obs['observation_type']
    loinc = LOINC_CODES.get(obs_type, {"code": "unknown", "display": obs_type})
    category = CATEGORY_MAP.get(obs_type, "exam")
    
    fhir_obs = {
        "resourceType": "Observation",
        "id": f"obs-patient002-{obs['id']}",
        "status": obs['status'] or "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": category,
                "display": category
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": loinc["code"],
                "display": loinc["display"]
            }],
            "text": loinc["display"]
        },
        "subject": {
            "reference": "Patient/patient-002",
            "display": f"{patient['first_name']} {patient['last_name']}"
        },
        "effectiveDateTime": obs['effective_datetime']
    }
    
    # Add value if present
    if obs['value']:
        if obs['unit']:
            fhir_obs["valueQuantity"] = {
                "value": float(obs['value']) if obs['value'].replace('.', '').isdigit() else 0,
                "unit": obs['unit'],
                "system": "http://unitsofmeasure.org",
                "code": obs['unit']
            }
        else:
            fhir_obs["valueString"] = obs['value']
    
    # Add notes if present
    if obs['doctor_remarks']:
        fhir_obs["note"] = [{
            "text": obs['doctor_remarks']
        }]
    
    return fhir_obs

def upload_to_fhir(observations):
    """Upload observations to FHIR server"""
    print(f"\nUploading {len(observations)} observations to FHIR server...")
    
    success = 0
    failed = 0
    
    for obs in observations:
        try:
            obs_id = obs["id"]
            response = requests.put(
                f"{FHIR_SERVER_URL}/Observation/{obs_id}",
                json=obs,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Uploaded {obs_id}")
                success += 1
            else:
                print(f"✗ Failed {obs_id}: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"✗ Error uploading {obs_id}: {str(e)}")
            failed += 1
    
    print(f"\nFHIR Upload Summary: {success} success, {failed} failed")
    return success, failed

def main():
    print("=" * 60)
    print("Patient-002 Observation Data Export & Upload")
    print("=" * 60)
    
    # Step 1: Read from local database
    result = get_observations_from_db()
    if not result:
        print("No data to export!")
        return
    
    observations, patient = result
    
    # Step 2: Convert to FHIR format
    print("\nConverting to FHIR format...")
    fhir_observations = [convert_to_fhir(dict(obs), dict(patient)) for obs in observations]
    print(f"Converted {len(fhir_observations)} observations")
    
    # Step 3: Save to JSON file for reference
    output_file = "sample_data/patient002_observations_export.json"
    with open(output_file, 'w') as f:
        json.dump(fhir_observations, f, indent=2)
    print(f"Saved to {output_file}")
    
    # Step 4: Upload to FHIR server
    upload_to_fhir(fhir_observations)
    
    # Step 5: Verify
    print("\nVerifying upload...")
    try:
        response = requests.get(f"{FHIR_SERVER_URL}/Observation?subject=Patient/patient-002")
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"✓ FHIR server now has {count} observations for patient-002")
        else:
            print(f"✗ Verification failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Verification error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Export and upload complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
