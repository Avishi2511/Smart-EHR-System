from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from app.database import get_db
from app import crud
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.condition import Condition
from fhir.resources.medication import Medication
from fhir.resources.encounter import Encounter
from fhir.resources.procedure import Procedure
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.immunization import Immunization
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.practitioner import Practitioner
import json
from datetime import date, datetime

router = APIRouter()

# Supported FHIR resource types
SUPPORTED_RESOURCES = {
    "Patient": Patient,
    "Observation": Observation,
    "Condition": Condition,
    "Medication": Medication,
    "Encounter": Encounter,
    "Procedure": Procedure,
    "AllergyIntolerance": AllergyIntolerance,
    "Immunization": Immunization,
    "MedicationRequest": MedicationRequest,
    "Practitioner": Practitioner
}

def serialize_dates(obj):
    """Recursively convert date/datetime objects to strings for JSON serialization"""
    if isinstance(obj, dict):
        return {key: serialize_dates(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(item) for item in obj]
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

def validate_fhir_resource(resource_type: str, resource_data: Dict[Any, Any]):
    """Validate FHIR resource using fhir.resources"""
    if resource_type not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")
    
    try:
        resource_class = SUPPORTED_RESOURCES[resource_type]
        validated_resource = resource_class(**resource_data)
        validated_dict = validated_resource.dict()
        
        # Serialize any date objects to strings for JSON storage
        serialized_dict = serialize_dates(validated_dict)
        return serialized_dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid FHIR resource: {str(e)}")

@router.post("/{resource_type}")
async def create_resource(
    resource_type: str, 
    resource_data: Dict[Any, Any],
    db: Session = Depends(get_db)
):
    """Create a new FHIR resource"""
    try:
        # Validate resource using fhir.resources
        validated_data = validate_fhir_resource(resource_type, resource_data)
        
        # Create in database
        db_resource = crud.create_resource(db, resource_type, validated_data)
        return db_resource.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{resource_type}/{resource_id}")
async def get_resource(
    resource_type: str, 
    resource_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific FHIR resource by ID"""
    if resource_type not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")
    
    resource = crud.get_resource(db, resource_type, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource.data

@router.get("/{resource_type}")
async def search_resources(
    resource_type: str,
    db: Session = Depends(get_db),
    _count: Optional[int] = Query(20, le=100),
    _offset: Optional[int] = Query(0, ge=0),
    # Patient search parameters
    name: Optional[str] = Query(None),
    family: Optional[str] = Query(None),
    given: Optional[str] = Query(None),
    birthdate: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    # Observation search parameters  
    patient: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    # Condition search parameters
    subject: Optional[str] = Query(None),
    # Encounter search parameters
    status: Optional[str] = Query(None)
):
    """Search FHIR resources with parameters"""
    
    if resource_type not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")
    
    # Build search parameters
    search_params = {}
    if name:
        search_params['name'] = name
    if family:
        search_params['family'] = family
    if given:
        search_params['given'] = given
    if birthdate:
        search_params['birthdate'] = birthdate
    if gender:
        search_params['gender'] = gender
    if patient:
        search_params['patient'] = patient
    if subject:
        search_params['patient'] = subject  # subject is alias for patient
    if code:
        search_params['code'] = code
    if date:
        search_params['date'] = date
    if status:
        search_params['status'] = status
    
    try:
        resources, total = crud.search_resources(
            db, resource_type, search_params, _count, _offset
        )
        
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": total,
            "entry": [{"resource": resource.data} for resource in resources]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{resource_type}/{resource_id}")
async def update_resource(
    resource_type: str,
    resource_id: str,
    resource_data: Dict[Any, Any],
    db: Session = Depends(get_db)
):
    """Update a FHIR resource"""
    try:
        # Validate resource
        validated_data = validate_fhir_resource(resource_type, resource_data)
        
        # Update in database
        updated_resource = crud.update_resource(db, resource_type, resource_id, validated_data)
        if not updated_resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return updated_resource.data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{resource_type}/{resource_id}")
async def delete_resource(
    resource_type: str,
    resource_id: str,
    db: Session = Depends(get_db)
):
    """Delete a FHIR resource"""
    if resource_type not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")
    
    success = crud.delete_resource(db, resource_type, resource_id)
    if not success:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    return {"message": "Resource deleted successfully"}

# Additional utility endpoints
@router.get("/_search/{resource_type}")
async def search_resources_post(
    resource_type: str,
    db: Session = Depends(get_db)
):
    """Alternative search endpoint (GET version of POST search)"""
    if resource_type not in SUPPORTED_RESOURCES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")
    
    resources = crud.get_all_resources_by_type(db, resource_type)
    
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [{"resource": resource.data} for resource in resources]
    }
