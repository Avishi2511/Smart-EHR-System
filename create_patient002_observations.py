"""
Create and upload 118 comprehensive observations for patient-002 (Priya Sharma, 35)
Includes Supabase links for documents and imaging
"""

import requests
import json
from datetime import datetime, timedelta
import random

# Configuration
FHIR_SERVER_URL = "https://smart-ehr-fhir-server.onrender.com"
SUPABASE_URL = "https://nhvltmiccxfwbsghcufm.supabase.co"
SUPABASE_BUCKET = "files"

# Patient info
PATIENT_ID = "patient-002"
PATIENT_NAME = "Priya Sharma"
PATIENT_AGE = 35

# LOINC code mappings
LOINC_CODES = {
    "glucose": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood", "unit": "mg/dL", "range": (90, 145)},
    "hba1c": {"code": "4548-4", "display": "Hemoglobin A1c", "unit": "%", "range": (5.5, 7.2)},
    "creatinine": {"code": "2160-0", "display": "Creatinine", "unit": "mg/dL", "range": (0.7, 1.2)},
    "heart_rate": {"code": "8867-4", "display": "Heart rate", "unit": "/min", "range": (65, 85)},
    "bp_systolic": {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg", "range": (120, 140)},
    "bp_diastolic": {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg", "range": (75, 90)},
    "temperature": {"code": "8310-5", "display": "Body temperature", "unit": "Cel", "range": (36.5, 37.5)},
    "weight": {"code": "29463-7", "display": "Body Weight", "unit": "kg", "range": (65, 72)},
    "height": {"code": "8302-2", "display": "Body Height", "unit": "cm", "range": (160, 165)},
}

IMAGING_CODES = {
    "mri": {"code": "24627-2", "display": "MRI Brain"},
    "pet": {"code": "44139-4", "display": "PET scan whole body"},
    "ct_scan": {"code": "24627-2", "display": "CT Head"},
}

VISIT_CODES = {
    "general_visit": {"code": "34117-2", "display": "History and physical note"},
    "eye_checkup": {"code": "70004-7", "display": "Ophthalmology Evaluation note"},
    "ent": {"code": "34879-7", "display": "Otolaryngology Evaluation note"},
    "alzheimer": {"code": "72107-6", "display": "Cognitive function assessment"},
}

def create_lab_observation(obs_type, date, value=None):
    """Create a lab observation"""
    config = LOINC_CODES[obs_type]
    
    if value is None:
        if obs_type == "hba1c":
            value = round(random.uniform(config["range"][0], config["range"][1]), 1)
        elif obs_type == "creatinine":
            value = round(random.uniform(config["range"][0], config["range"][1]), 1)
        else:
            value = random.randint(int(config["range"][0]), int(config["range"][1]))
    
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "laboratory",
                "display": "Laboratory"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": config["code"],
                "display": config["display"]
            }],
            "text": config["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}",
            "display": PATIENT_NAME
        },
        "effectiveDateTime": date.isoformat() + "Z",
        "valueQuantity": {
            "value": value,
            "unit": config["unit"],
            "system": "http://unitsofmeasure.org",
            "code": config["unit"]
        }
    }

def create_vital_observation(obs_type, date, value=None):
    """Create a vital signs observation"""
    config = LOINC_CODES[obs_type]
    
    if value is None:
        if obs_type == "temperature":
            value = round(random.uniform(config["range"][0], config["range"][1]), 1)
        else:
            value = random.randint(int(config["range"][0]), int(config["range"][1]))
    
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs",
                "display": "Vital Signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": config["code"],
                "display": config["display"]
            }],
            "text": config["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}",
            "display": PATIENT_NAME
        },
        "effectiveDateTime": date.isoformat() + "Z",
        "valueQuantity": {
            "value": value,
            "unit": config["unit"],
            "system": "http://unitsofmeasure.org",
            "code": config["unit"]
        }
    }

def create_imaging_observation(imaging_type, date, scan_number):
    """Create an imaging observation with Supabase link"""
    config = IMAGING_CODES[imaging_type]
    
    # Create Supabase storage link
    file_path = f"medical-images/{PATIENT_ID}/{imaging_type}/{imaging_type}_scan_{scan_number}.pdf"
    supabase_link = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
    
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "imaging",
                "display": "Imaging"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": config["code"],
                "display": config["display"]
            }],
            "text": config["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}",
            "display": PATIENT_NAME
        },
        "effectiveDateTime": date.isoformat() + "Z",
        "valueString": "Scan completed",
        "note": [{
            "text": f"Imaging report available at: {supabase_link}"
        }],
        "component": [{
            "code": {
                "text": "Report Link"
            },
            "valueString": supabase_link
        }]
    }

def create_visit_observation(visit_type, date, visit_number):
    """Create a clinical visit observation with Supabase document link"""
    config = VISIT_CODES[visit_type]
    
    # Create Supabase storage link for visit notes
    file_path = f"clinical-documents/{PATIENT_ID}/visits/{visit_type}_visit_{visit_number}.pdf"
    supabase_link = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
    
    remarks = [
        "Patient reports feeling well",
        "Overall health status good",
        "Continue current medications",
        "Routine follow-up recommended",
        "Minor concerns addressed"
    ]
    
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "exam",
                "display": "Exam"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": config["code"],
                "display": config["display"]
            }],
            "text": config["display"]
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}",
            "display": PATIENT_NAME
        },
        "effectiveDateTime": date.isoformat() + "Z",
        "valueString": "Visit completed",
        "note": [{
            "text": f"{random.choice(remarks)}. Clinical notes: {supabase_link}"
        }],
        "component": [{
            "code": {
                "text": "Clinical Notes Link"
            },
            "valueString": supabase_link
        }]
    }

def create_document_observation(date, doc_number):
    """Create a clinical document observation with Supabase link"""
    file_path = f"clinical-documents/{PATIENT_ID}/general/clinical_doc_{doc_number}.pdf"
    supabase_link = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
    
    doc_types = [
        "Lab results reviewed and filed",
        "Consultation notes from specialist",
        "Discharge summary on file",
        "Imaging report archived",
        "Prescription record"
    ]
    
    return {
        "resourceType": "Observation",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "procedure",
                "display": "Procedure"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": "34133-9",
                "display": "Clinical Document"
            }],
            "text": "Clinical Document"
        },
        "subject": {
            "reference": f"Patient/{PATIENT_ID}",
            "display": PATIENT_NAME
        },
        "effectiveDateTime": date.isoformat() + "Z",
        "valueString": "Document uploaded",
        "note": [{
            "text": f"{random.choice(doc_types)}. Document link: {supabase_link}"
        }],
        "component": [{
            "code": {
                "text": "Document Link"
            },
            "valueString": supabase_link
        }]
    }

def generate_all_observations():
    """Generate all 118 observations"""
    observations = []
    current_date = datetime.now()
    
    print(f"Generating observations for {PATIENT_NAME} (patient-002, age {PATIENT_AGE})...")
    
    # 1. Lab results (every 2 months for 2 years) = 12 * 3 types = 36 observations
    print("  Generating lab results...")
    for months_back in range(0, 24, 2):
        obs_date = current_date - timedelta(days=months_back * 30)
        observations.append(create_lab_observation("glucose", obs_date))
        observations.append(create_lab_observation("hba1c", obs_date))
        observations.append(create_lab_observation("creatinine", obs_date))
    
    # 2. Vital signs (monthly for 2 years) = 24 * 5 types = 120, but we'll do 72 (18 months * 4 types)
    print("  Generating vital signs...")
    for months_back in range(0, 18):
        obs_date = current_date - timedelta(days=months_back * 30 + random.randint(0, 15))
        observations.append(create_vital_observation("heart_rate", obs_date))
        observations.append(create_vital_observation("bp_systolic", obs_date))
        observations.append(create_vital_observation("bp_diastolic", obs_date))
        observations.append(create_vital_observation("temperature", obs_date))
    
    # 3. Imaging scans (6 scans over 3 years)
    print("  Generating imaging scans...")
    imaging_dates = [6, 12, 18, 24, 30, 36]
    for i, months_back in enumerate(imaging_dates[:6]):
        obs_date = current_date - timedelta(days=months_back * 30)
        imaging_type = random.choice(list(IMAGING_CODES.keys()))
        observations.append(create_imaging_observation(imaging_type, obs_date, i+1))
    
    # 4. Clinical visits (8 visits over 2 years, quarterly)
    print("  Generating clinical visits...")
    for i, months_back in enumerate(range(0, 24, 3)):
        obs_date = current_date - timedelta(days=months_back * 30 + random.randint(0, 20))
        visit_type = random.choice(list(VISIT_CODES.keys()))
        observations.append(create_visit_observation(visit_type, obs_date, i+1))
    
    # 5. Clinical documents (4 documents)
    print("  Generating clinical documents...")
    for i, months_back in enumerate([1, 6, 12, 18]):
        obs_date = current_date - timedelta(days=months_back * 30)
        observations.append(create_document_observation(obs_date, i+1))
    
    print(f"  Total generated: {len(observations)} observations")
    return observations

def upload_to_fhir(observations):
    """Upload observations to FHIR server using POST"""
    print(f"\nUploading {len(observations)} observations to FHIR server...")
    print(f"Target: {FHIR_SERVER_URL}")
    
    success = 0
    failed = 0
    
    for i, obs in enumerate(observations, 1):
        try:
            response = requests.post(
                f"{FHIR_SERVER_URL}/Observation",
                json=obs,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"  [{i}/{len(observations)}] ✓ Uploaded {obs['code']['text']}")
                success += 1
            else:
                print(f"  [{i}/{len(observations)}] ✗ Failed {obs['code']['text']}: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"  [{i}/{len(observations)}] ✗ Error: {str(e)}")
            failed += 1
    
    print(f"\nUpload Summary:")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    return success, failed

def verify_upload():
    """Verify observations were uploaded"""
    print("\nVerifying upload...")
    try:
        response = requests.get(
            f"{FHIR_SERVER_URL}/Observation?subject=Patient/{PATIENT_ID}",
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get('total', 0)
            print(f"✓ FHIR server now has {count} observations for {PATIENT_NAME}")
            return count
        else:
            print(f"✗ Verification failed: {response.status_code}")
            return 0
    except Exception as e:
        print(f"✗ Verification error: {str(e)}")
        return 0

def main():
    print("=" * 70)
    print(f"Creating Comprehensive Observations for {PATIENT_NAME}")
    print(f"Patient ID: {PATIENT_ID} | Age: {PATIENT_AGE}")
    print("=" * 70)
    
    # Generate observations
    observations = generate_all_observations()
    
    # Save to file
    output_file = f"sample_data/{PATIENT_ID}_comprehensive_observations.json"
    with open(output_file, 'w') as f:
        json.dump(observations, f, indent=2)
    print(f"\n✓ Saved to {output_file}")
    
    # Upload to FHIR server
    success, failed = upload_to_fhir(observations)
    
    # Verify
    total = verify_upload()
    
    print("\n" + "=" * 70)
    print("Complete!")
    print(f"Generated: {len(observations)} observations")
    print(f"Uploaded: {success} observations")
    print(f"Total in FHIR: {total} observations for {PATIENT_NAME}")
    print("=" * 70)

if __name__ == "__main__":
    main()
