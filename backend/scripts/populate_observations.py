"""
Script to populate comprehensive observation data for patient-002
Includes lab results, vitals, imaging, clinical visits, and documents
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.sql_models import Observation, Patient


# Observation type definitions
OBSERVATION_TYPES = {
    # Lab results
    "glucose": {"unit": "mg/dL", "range": (70, 140), "remarks_chance": 0.3},
    "hba1c": {"unit": "%", "range": (5.0, 7.0), "remarks_chance": 0.4},
    "creatinine": {"unit": "mg/dL", "range": (0.7, 1.3), "remarks_chance": 0.2},
    
    # Vital signs
    "heart_rate": {"unit": "bpm", "range": (60, 100), "remarks_chance": 0.1},
    "bp_systolic": {"unit": "mmHg", "range": (110, 135), "remarks_chance": 0.2},
    "bp_diastolic": {"unit": "mmHg", "range": (70, 85), "remarks_chance": 0.2},
    
    # Imaging
    "mri": {"unit": None, "value": "Scan completed", "remarks_chance": 0.9},
    "pet": {"unit": None, "value": "Scan completed", "remarks_chance": 0.9},
    "ct_scan": {"unit": None, "value": "Scan completed", "remarks_chance": 0.9},
    
    # Clinical visits
    "general_visit": {"unit": None, "value": "Routine checkup", "remarks_chance": 0.7},
    "eye_checkup": {"unit": None, "value": "Vision assessment", "remarks_chance": 0.6},
    "ent": {"unit": None, "value": "ENT examination", "remarks_chance": 0.5},
    "alzheimer": {"unit": None, "value": "Cognitive assessment", "remarks_chance": 0.8},
    
    # Documents
    "clinical_document": {"unit": None, "value": "Document uploaded", "remarks_chance": 0.5},
}

# Doctor remarks templates
REMARKS_TEMPLATES = {
    "glucose": [
        "Fasting glucose levels within normal range",
        "Slightly elevated, recommend dietary modifications",
        "Monitor glucose levels regularly",
        "Pre-diabetic range, lifestyle changes recommended"
    ],
    "hba1c": [
        "Good glycemic control maintained",
        "HbA1c trending upward, increase monitoring",
        "Excellent diabetes management",
        "Consider medication adjustment"
    ],
    "creatinine": [
        "Kidney function normal",
        "Slight elevation, monitor hydration",
        "Stable renal function",
        "Within acceptable range for age"
    ],
    "heart_rate": [
        "Normal sinus rhythm",
        "Slightly elevated, check for anxiety",
        "Resting heart rate optimal",
        "Consider beta-blocker if persistent"
    ],
    "bp_systolic": [
        "Blood pressure well controlled",
        "Borderline hypertension, lifestyle modifications advised",
        "Excellent BP control",
        "Monitor closely, may need medication adjustment"
    ],
    "mri": [
        "MRI brain shows age-appropriate changes",
        "No acute abnormalities detected",
        "Mild cortical atrophy noted",
        "Hippocampal volume within normal limits",
        "Small vessel disease changes present"
    ],
    "pet": [
        "PET scan shows normal metabolic activity",
        "Mild hypometabolism in temporal lobes",
        "No significant amyloid deposition",
        "Pattern consistent with early cognitive changes"
    ],
    "ct_scan": [
        "CT chest clear, no abnormalities",
        "No acute findings",
        "Age-appropriate changes only",
        "Follow-up recommended in 6 months"
    ],
    "general_visit": [
        "Overall health status good",
        "Continue current medications",
        "Routine follow-up in 3 months",
        "Patient reports feeling well",
        "Minor concerns addressed"
    ],
    "eye_checkup": [
        "Vision stable, no changes needed",
        "Early cataract formation noted",
        "Retinal examination normal",
        "Prescription updated",
        "No diabetic retinopathy detected"
    ],
    "ent": [
        "Hearing within normal limits",
        "Mild hearing loss in high frequencies",
        "No sinus abnormalities",
        "Tinnitus reported, monitoring advised"
    ],
    "alzheimer": [
        "Cognitive function stable",
        "MMSE score: 28/30 - mild impairment",
        "Memory complaints noted, continue monitoring",
        "Recommend cognitive exercises",
        "Family reports no significant changes"
    ],
    "clinical_document": [
        "Lab results reviewed and filed",
        "Consultation notes from specialist",
        "Discharge summary on file",
        "Imaging report archived"
    ]
}

# Medication templates
MEDICATIONS = {
    "glucose": ["Metformin 500mg twice daily", "Glipizide 5mg once daily", None],
    "hba1c": ["Continue Metformin", "Increase Metformin to 1000mg", None],
    "bp_systolic": ["Lisinopril 10mg daily", "Amlodipine 5mg daily", None],
    "bp_diastolic": ["Continue current BP medication", None],
    "alzheimer": ["Donepezil 10mg daily", "Memantine 10mg twice daily", "Vitamin E 400 IU daily"],
    "general_visit": ["Multivitamin daily", "Aspirin 81mg daily", None],
}


def generate_value(obs_type, config):
    """Generate a realistic value for an observation"""
    if "value" in config:
        return config["value"]
    
    if "range" in config:
        min_val, max_val = config["range"]
        if obs_type == "hba1c":
            return str(round(random.uniform(min_val, max_val), 1))
        else:
            return str(random.randint(int(min_val), int(max_val)))
    
    return None


def get_doctor_remarks(obs_type, remarks_chance):
    """Get doctor remarks based on observation type"""
    if random.random() > remarks_chance:
        return None
    
    if obs_type in REMARKS_TEMPLATES:
        return random.choice(REMARKS_TEMPLATES[obs_type])
    
    return None


def get_medication(obs_type):
    """Get medication prescription"""
    if obs_type in MEDICATIONS:
        med = random.choice(MEDICATIONS[obs_type])
        return med
    return None


def generate_document_link(obs_type, obs_id):
    """Generate mock document link for imaging/documents"""
    if obs_type in ["mri", "pet", "ct_scan", "clinical_document"]:
        return f"/documents/{obs_type}/{obs_id}.pdf"
    return None


def populate_observations():
    """Populate comprehensive observation data for patient-002"""
    db = SessionLocal()
    
    try:
        # Find patient-002
        patient = db.query(Patient).filter(Patient.fhir_id == "patient-002").first()
        
        if not patient:
            print("Patient-002 not found. Creating...")
            patient = Patient(
                fhir_id="patient-002",
                first_name="Jane",
                last_name="Smith",
                gender="female"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
            print(f"Created patient: {patient.id}")
        else:
            print(f"Found patient: {patient.id}")
        
        # Delete existing observations
        db.query(Observation).filter(Observation.patient_id == patient.id).delete()
        db.commit()
        print("Cleared existing observations")
        
        current_date = datetime.now()
        observations_to_add = []
        
        # Generate lab results (30-40 observations over 2 years)
        lab_types = ["glucose", "hba1c", "creatinine"]
        for months_back in range(0, 24, 2):  # Every 2 months
            obs_date = current_date - timedelta(days=months_back * 30)
            for lab_type in lab_types:
                if random.random() > 0.3:  # 70% chance of having this lab
                    config = OBSERVATION_TYPES[lab_type]
                    obs = Observation(
                        patient_id=patient.id,
                        observation_type=lab_type,
                        value=generate_value(lab_type, config),
                        unit=config.get("unit"),
                        effective_datetime=obs_date,
                        doctor_remarks=get_doctor_remarks(lab_type, config["remarks_chance"]),
                        medication_prescribed=get_medication(lab_type),
                        status="final"
                    )
                    observations_to_add.append(obs)
        
        # Generate vital signs (50+ observations)
        vital_types = ["heart_rate", "bp_systolic", "bp_diastolic"]
        for months_back in range(0, 24, 1):  # Monthly
            obs_date = current_date - timedelta(days=months_back * 30 + random.randint(0, 15))
            for vital_type in vital_types:
                config = OBSERVATION_TYPES[vital_type]
                obs = Observation(
                    patient_id=patient.id,
                    observation_type=vital_type,
                    value=generate_value(vital_type, config),
                    unit=config.get("unit"),
                    effective_datetime=obs_date,
                    doctor_remarks=get_doctor_remarks(vital_type, config["remarks_chance"]),
                    medication_prescribed=get_medication(vital_type),
                    status="final"
                )
                observations_to_add.append(obs)
        
        # Generate imaging scans (5-10 scans)
        imaging_types = ["mri", "pet", "ct_scan"]
        imaging_dates = [6, 12, 18, 24, 30, 36]  # Every 6 months going back 3 years
        for months_back in imaging_dates[:random.randint(5, 8)]:
            obs_date = current_date - timedelta(days=months_back * 30)
            imaging_type = random.choice(imaging_types)
            config = OBSERVATION_TYPES[imaging_type]
            obs_id = f"{imaging_type}_{months_back}"
            obs = Observation(
                patient_id=patient.id,
                observation_type=imaging_type,
                value=config.get("value"),
                unit=config.get("unit"),
                effective_datetime=obs_date,
                doctor_remarks=get_doctor_remarks(imaging_type, config["remarks_chance"]),
                medication_prescribed=None,
                document_link=generate_document_link(imaging_type, obs_id),
                status="final"
            )
            observations_to_add.append(obs)
        
        # Generate clinical visits (15-20 visits)
        visit_types = ["general_visit", "eye_checkup", "ent", "alzheimer"]
        for months_back in range(0, 24, 3):  # Quarterly
            obs_date = current_date - timedelta(days=months_back * 30 + random.randint(0, 20))
            visit_type = random.choice(visit_types)
            config = OBSERVATION_TYPES[visit_type]
            obs = Observation(
                patient_id=patient.id,
                observation_type=visit_type,
                value=config.get("value"),
                unit=config.get("unit"),
                effective_datetime=obs_date,
                doctor_remarks=get_doctor_remarks(visit_type, config["remarks_chance"]),
                medication_prescribed=get_medication(visit_type),
                status="final"
            )
            observations_to_add.append(obs)
        
        # Generate clinical documents (10-15 documents)
        for months_back in [1, 3, 5, 7, 9, 12, 15, 18, 21, 24]:
            obs_date = current_date - timedelta(days=months_back * 30)
            config = OBSERVATION_TYPES["clinical_document"]
            obs_id = f"doc_{months_back}"
            obs = Observation(
                patient_id=patient.id,
                observation_type="clinical_document",
                value=config.get("value"),
                unit=config.get("unit"),
                effective_datetime=obs_date,
                doctor_remarks=get_doctor_remarks("clinical_document", config["remarks_chance"]),
                medication_prescribed=None,
                document_link=generate_document_link("clinical_document", obs_id),
                status="final"
            )
            observations_to_add.append(obs)
        
        # Bulk insert
        db.bulk_save_objects(observations_to_add)
        db.commit()
        
        # Print summary
        print(f"\n✓ Successfully added {len(observations_to_add)} observations")
        
        # Count by type
        type_counts = {}
        for obs in observations_to_add:
            type_counts[obs.observation_type] = type_counts.get(obs.observation_type, 0) + 1
        
        print("\nObservations by type:")
        for obs_type, count in sorted(type_counts.items()):
            print(f"  - {obs_type}: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_observations()
