from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.sql_models import Patient, File, Parameter, ModelResult
from app.models.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientDetailResponse
)
from app.services.fhir_service import fhir_service
from app.services.parameter_extractor import parameter_extractor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new patient
    
    Creates a patient record linked to FHIR ID and optionally NFC card ID.
    Fetches demographics from FHIR server if available.
    """
    # Check if patient with FHIR ID already exists
    existing = db.query(Patient).filter(Patient.fhir_id == patient.fhir_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Patient with FHIR ID {patient.fhir_id} already exists"
        )
    
    # Check if NFC card ID is already used
    if patient.nfc_card_id:
        existing_nfc = db.query(Patient).filter(Patient.nfc_card_id == patient.nfc_card_id).first()
        if existing_nfc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"NFC card ID {patient.nfc_card_id} already in use"
            )
    
    # Fetch patient data from FHIR if not provided
    if not patient.first_name or not patient.last_name:
        fhir_patient = await fhir_service.get_patient(patient.fhir_id)
        if fhir_patient:
            name = fhir_patient.get("name", [{}])[0]
            patient.first_name = patient.first_name or name.get("given", [""])[0]
            patient.last_name = patient.last_name or name.get("family", "")
            patient.gender = patient.gender or fhir_patient.get("gender")
            
            # Parse birth date
            if not patient.date_of_birth and fhir_patient.get("birthDate"):
                from datetime import datetime
                patient.date_of_birth = datetime.fromisoformat(fhir_patient["birthDate"])
    
    # Create patient
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    
    logger.info(f"Created patient {db_patient.id} with FHIR ID {db_patient.fhir_id}")
    
    return db_patient


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get patient details
    
    Returns patient information merged from SQL and FHIR server.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Get FHIR data
    fhir_data = await fhir_service.get_patient(patient.fhir_id)
    
    # Get counts
    total_files = db.query(File).filter(File.patient_id == patient_id).count()
    total_parameters = db.query(Parameter).filter(Parameter.patient_id == patient_id).count()
    total_model_runs = db.query(ModelResult).filter(ModelResult.patient_id == patient_id).count()
    
    return PatientDetailResponse(
        **patient.__dict__,
        fhir_data=fhir_data,
        total_files=total_files,
        total_parameters=total_parameters,
        total_model_runs=total_model_runs
    )


@router.get("/", response_model=List[PatientResponse])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all patients"""
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Update fields
    update_data = patient_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    db.commit()
    db.refresh(patient)
    
    logger.info(f"Updated patient {patient_id}")
    
    return patient


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Delete a patient and all associated data"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Delete from vector database
    from app.services.vector_db import vector_db
    vector_db.delete_by_patient(patient_id)
    
    # Delete from SQL (cascade will handle related records)
    db.delete(patient)
    db.commit()
    
    logger.info(f"Deleted patient {patient_id}")


@router.post("/{patient_id}/sync-fhir")
async def sync_patient_from_fhir(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Sync patient parameters from FHIR server
    
    Fetches all available clinical parameters from FHIR and stores them in SQL.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Sync parameters
    count = await parameter_extractor.sync_from_fhir(
        db=db,
        patient_id=patient_id,
        fhir_id=patient.fhir_id
    )
    
    return {
        "message": f"Synced {count} parameters from FHIR",
        "patient_id": patient_id,
        "parameters_synced": count
    }


@router.get("/by-nfc/{nfc_card_id}", response_model=PatientResponse)
async def get_patient_by_nfc(
    nfc_card_id: str,
    db: Session = Depends(get_db)
):
    """Get patient by NFC card ID"""
    patient = db.query(Patient).filter(Patient.nfc_card_id == nfc_card_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with NFC card ID {nfc_card_id} not found"
        )
    
    return patient


@router.get("/by-fhir/{fhir_id}", response_model=PatientResponse)
async def get_patient_by_fhir_id(
    fhir_id: str,
    db: Session = Depends(get_db)
):
    """Get patient by FHIR ID"""
    patient = db.query(Patient).filter(Patient.fhir_id == fhir_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with FHIR ID {fhir_id} not found"
        )
    
    return patient
