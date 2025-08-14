from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models import FHIRResource
from typing import Dict, Any, Tuple, List, Optional
import uuid
from datetime import datetime

def create_resource(db: Session, resource_type: str, resource_data: Dict[Any, Any]) -> FHIRResource:
    """Create a new FHIR resource"""
    # Ensure resource has an ID
    if 'id' not in resource_data:
        resource_data['id'] = str(uuid.uuid4())
    
    db_resource = FHIRResource(
        id=resource_data['id'],
        resource_type=resource_type,
        data=resource_data
    )
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return db_resource

def get_resource(db: Session, resource_type: str, resource_id: str) -> Optional[FHIRResource]:
    """Get a resource by type and ID"""
    return db.query(FHIRResource).filter(
        and_(
            FHIRResource.resource_type == resource_type,
            FHIRResource.id == resource_id
        )
    ).first()

def search_resources(
    db: Session, 
    resource_type: str, 
    search_params: Dict[str, str],
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[FHIRResource], int]:
    """Search resources with parameters"""
    
    query = db.query(FHIRResource).filter(FHIRResource.resource_type == resource_type)
    
    # Apply search parameters based on resource type
    if resource_type == "Patient":
        if 'name' in search_params:
            # Search in both given and family names
            name_filter = or_(
                func.json_extract(FHIRResource.data, '$.name[0].given[0]').like(f"%{search_params['name']}%"),
                func.json_extract(FHIRResource.data, '$.name[0].family').like(f"%{search_params['name']}%")
            )
            query = query.filter(name_filter)
        
        if 'family' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.name[0].family').like(f"%{search_params['family']}%")
            )
        
        if 'given' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.name[0].given[0]').like(f"%{search_params['given']}%")
            )
        
        if 'birthdate' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.birthDate') == search_params['birthdate']
            )
        
        if 'gender' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.gender') == search_params['gender']
            )
    
    elif resource_type == "Observation":
        if 'patient' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.subject.reference').like(f"%{search_params['patient']}%")
            )
        
        if 'code' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.code.text').like(f"%{search_params['code']}%")
            )
        
        if 'date' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.effectiveDateTime').like(f"%{search_params['date']}%")
            )
    
    elif resource_type == "Condition":
        if 'patient' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.subject.reference').like(f"%{search_params['patient']}%")
            )
        
        if 'code' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.code.text').like(f"%{search_params['code']}%")
            )
    
    elif resource_type == "Practitioner":
        if 'name' in search_params:
            # Search in both given and family names for practitioners
            name_filter = or_(
                func.json_extract(FHIRResource.data, '$.name[0].given[0]').like(f"%{search_params['name']}%"),
                func.json_extract(FHIRResource.data, '$.name[0].family').like(f"%{search_params['name']}%")
            )
            query = query.filter(name_filter)
        
        if 'family' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.name[0].family').like(f"%{search_params['family']}%")
            )
        
        if 'given' in search_params:
            query = query.filter(
                func.json_extract(FHIRResource.data, '$.name[0].given[0]').like(f"%{search_params['given']}%")
            )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    resources = query.offset(offset).limit(limit).all()
    
    return resources, total

def update_resource(
    db: Session, 
    resource_type: str, 
    resource_id: str, 
    resource_data: Dict[Any, Any]
) -> Optional[FHIRResource]:
    """Update a resource"""
    db_resource = get_resource(db, resource_type, resource_id)
    if db_resource:
        resource_data['id'] = resource_id  # Ensure ID consistency
        db_resource.data = resource_data
        db_resource.last_updated = datetime.utcnow()
        db.commit()
        db.refresh(db_resource)
    return db_resource

def delete_resource(db: Session, resource_type: str, resource_id: str) -> bool:
    """Delete a resource"""
    db_resource = get_resource(db, resource_type, resource_id)
    if db_resource:
        db.delete(db_resource)
        db.commit()
        return True
    return False

def get_all_resources_by_type(db: Session, resource_type: str) -> List[FHIRResource]:
    """Get all resources of a specific type"""
    return db.query(FHIRResource).filter(FHIRResource.resource_type == resource_type).all()
