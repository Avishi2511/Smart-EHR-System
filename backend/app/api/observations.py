from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.sql_models import Observation, Patient
from app.models.schemas import ObservationResponse, ObservationListResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Observations"])


@router.get("/observations/{patient_id}", response_model=ObservationListResponse)
async def get_observations(
    patient_id: str,
    limit: Optional[int] = Query(None, description="Limit number of observations"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    observation_type: Optional[str] = Query(None, description="Filter by observation type"),
    db: Session = Depends(get_db)
):
    """
    Get observations for a patient with optional filtering
    
    Filters:
    - limit: Number of most recent observations to return
    - start_date: Only observations after this date
    - end_date: Only observations before this date
    - observation_type: Filter by specific observation type
    """
    try:
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
        
        # Build query
        query = db.query(Observation).filter(Observation.patient_id == patient_id)
        
        # Apply filters
        if start_date:
            query = query.filter(Observation.effective_datetime >= start_date)
        
        if end_date:
            query = query.filter(Observation.effective_datetime <= end_date)
        
        if observation_type:
            query = query.filter(Observation.observation_type == observation_type)
        
        # Get total count before limit
        total_count = db.query(Observation).filter(Observation.patient_id == patient_id).count()
        filtered_count = query.count()
        
        # Order by most recent first
        query = query.order_by(Observation.effective_datetime.desc())
        
        # Apply limit
        if limit:
            query = query.limit(limit)
        
        observations = query.all()
        
        return ObservationListResponse(
            observations=[
                ObservationResponse(
                    id=obs.id,
                    patient_id=obs.patient_id,
                    observation_type=obs.observation_type,
                    value=obs.value,
                    unit=obs.unit,
                    effective_datetime=obs.effective_datetime,
                    doctor_remarks=obs.doctor_remarks,
                    medication_prescribed=obs.medication_prescribed,
                    document_link=obs.document_link,
                    status=obs.status
                )
                for obs in observations
            ],
            total=total_count,
            filtered=filtered_count
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching observations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/observations/{patient_id}/types", response_model=List[str])
async def get_observation_types(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get all unique observation types for a patient"""
    try:
        types = db.query(Observation.observation_type).filter(
            Observation.patient_id == patient_id
        ).distinct().all()
        
        return [t[0] for t in types]
    except Exception as e:
        logger.error(f"Error fetching observation types: {e}")
        raise HTTPException(status_code=500, detail=str(e))
