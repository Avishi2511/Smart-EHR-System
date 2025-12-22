from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.sql_models import Parameter
from app.models.schemas import ParameterResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Analytics"])


@router.get("/analytics/{patient_id}/hba1c", response_model=List[ParameterResponse])
async def get_hba1c_history(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get HbA1c history for a patient"""
    try:
        parameters = db.query(Parameter).filter(
            and_(
                Parameter.patient_id == patient_id,
                Parameter.parameter_name == "HbA1c"
            )
        ).order_by(Parameter.timestamp).all()
        
        if not parameters:
            logger.warning(f"No HbA1c data found for patient {patient_id}")
            return []
        
        return [
            ParameterResponse(
                id=p.id,
                patient_id=p.patient_id,
                parameter_name=p.parameter_name,
                value=p.value,
                unit=p.unit,
                source=p.source,
                source_id=p.source_id,
                timestamp=p.timestamp,
                created_at=p.created_at
            )
            for p in parameters
        ]
    except Exception as e:
        logger.error(f"Error fetching HbA1c data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{patient_id}/blood-pressure", response_model=List[dict])
async def get_blood_pressure_history(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get blood pressure history for a patient"""
    try:
        # Get systolic readings
        systolic = db.query(Parameter).filter(
            and_(
                Parameter.patient_id == patient_id,
                Parameter.parameter_name == "Systolic Blood Pressure"
            )
        ).order_by(Parameter.timestamp).all()
        
        # Get diastolic readings
        diastolic = db.query(Parameter).filter(
            and_(
                Parameter.patient_id == patient_id,
                Parameter.parameter_name == "Diastolic Blood Pressure"
            )
        ).order_by(Parameter.timestamp).all()
        
        if not systolic or not diastolic:
            logger.warning(f"No blood pressure data found for patient {patient_id}")
            return []
        
        # Combine systolic and diastolic readings by timestamp
        bp_data = []
        systolic_dict = {p.timestamp: p for p in systolic}
        diastolic_dict = {p.timestamp: p for p in diastolic}
        
        # Get all unique timestamps
        all_timestamps = sorted(set(systolic_dict.keys()) | set(diastolic_dict.keys()))
        
        for ts in all_timestamps:
            if ts in systolic_dict and ts in diastolic_dict:
                bp_data.append({
                    "timestamp": ts,
                    "systolic": systolic_dict[ts].value,
                    "diastolic": diastolic_dict[ts].value,
                    "unit": systolic_dict[ts].unit
                })
        
        return bp_data
    except Exception as e:
        logger.error(f"Error fetching blood pressure data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
