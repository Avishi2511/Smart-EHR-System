"""
Script to populate mock analytics data for patient-002
Adds HbA1c and Blood Pressure readings over 7-10 years
"""
import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.sql_models import Parameter, Patient, DataSource


def populate_analytics_data():
    """Populate analytics data for patient-002"""
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
        
        # Delete existing analytics data for this patient
        db.query(Parameter).filter(
            Parameter.patient_id == patient.id
        ).filter(
            Parameter.parameter_name.in_([
                "HbA1c",
                "Systolic Blood Pressure",
                "Diastolic Blood Pressure"
            ])
        ).delete(synchronize_session=False)
        db.commit()
        print("Cleared existing analytics data")
        
        # Generate data for the last 8 years with 2-3 readings per year
        current_date = datetime.now()
        years = 8
        readings_per_year = [2, 3, 2, 3, 2, 3, 2, 3]  # Alternating 2-3 readings
        
        # Starting values
        hba1c_base = 5.4  # Starting HbA1c (normal range: 4-5.6%)
        hba1c_increment = 0.15  # Gradual increase per year
        
        parameters_to_add = []
        
        for year_offset in range(years):
            num_readings = readings_per_year[year_offset]
            year_start = current_date - timedelta(days=365 * (years - year_offset))
            
            for reading in range(num_readings):
                # Distribute readings throughout the year
                days_offset = (365 // (num_readings + 1)) * (reading + 1)
                reading_date = year_start + timedelta(days=days_offset)
                
                # HbA1c - gradual increase with some variation
                hba1c_value = hba1c_base + (year_offset * hba1c_increment) + random.uniform(-0.1, 0.1)
                hba1c_value = round(hba1c_value, 1)
                
                # Blood Pressure - random normal values
                # Normal ranges: Systolic 110-130, Diastolic 70-85
                systolic = random.randint(110, 130)
                diastolic = random.randint(70, 85)
                
                # Add HbA1c parameter
                parameters_to_add.append(Parameter(
                    patient_id=patient.id,
                    parameter_name="HbA1c",
                    value=hba1c_value,
                    unit="%",
                    source=DataSource.MANUAL,
                    timestamp=reading_date
                ))
                
                # Add Systolic BP parameter
                parameters_to_add.append(Parameter(
                    patient_id=patient.id,
                    parameter_name="Systolic Blood Pressure",
                    value=systolic,
                    unit="mmHg",
                    source=DataSource.MANUAL,
                    timestamp=reading_date
                ))
                
                # Add Diastolic BP parameter
                parameters_to_add.append(Parameter(
                    patient_id=patient.id,
                    parameter_name="Diastolic Blood Pressure",
                    value=diastolic,
                    unit="mmHg",
                    source=DataSource.MANUAL,
                    timestamp=reading_date
                ))
                
                print(f"Year {years - year_offset}, Reading {reading + 1}: "
                      f"Date={reading_date.strftime('%Y-%m-%d')}, "
                      f"HbA1c={hba1c_value}%, BP={systolic}/{diastolic}")
        
        # Bulk insert all parameters
        db.bulk_save_objects(parameters_to_add)
        db.commit()
        
        print(f"\n✓ Successfully added {len(parameters_to_add)} parameter readings")
        print(f"  - {len(parameters_to_add) // 3} HbA1c readings")
        print(f"  - {len(parameters_to_add) // 3} Blood Pressure readings")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_analytics_data()
