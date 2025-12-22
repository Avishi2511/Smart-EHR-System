from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.sql_models import Parameter, DataSource
from app.models.schemas import (
    ParameterQueryRequest,
    ParameterQueryResponse,
    ParameterResponse
)
from app.services.parameter_extractor import parameter_extractor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queries", tags=["Queries"])


@router.post("/parameters", response_model=ParameterQueryResponse)
async def query_parameters(
    request: ParameterQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query specific parameters for a patient
    
    Returns parameter values from SQL database within optional date range.
    """
    query = db.query(Parameter).filter(Parameter.patient_id == request.patient_id)
    
    # Filter by parameter names
    if request.parameter_names:
        query = query.filter(Parameter.parameter_name.in_(request.parameter_names))
    
    # Filter by date range
    if request.start_date:
        query = query.filter(Parameter.timestamp >= request.start_date)
    
    if request.end_date:
        query = query.filter(Parameter.timestamp <= request.end_date)
    
    parameters = query.order_by(Parameter.timestamp.desc()).all()
    
    return ParameterQueryResponse(
        patient_id=request.patient_id,
        parameters=[ParameterResponse.model_validate(p) for p in parameters]
    )


@router.get("/parameters/{patient_id}/latest")
async def get_latest_parameters(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get the most recent value for each parameter for a patient"""
    latest = parameter_extractor.get_latest_parameters(db, patient_id)
    
    return {
        "patient_id": patient_id,
        "parameters": {
            name: {
                "value": param.value,
                "unit": param.unit,
                "timestamp": param.timestamp.isoformat(),
                "source": param.source.value
            }
            for name, param in latest.items()
        }
    }


@router.get("/parameters/{patient_id}/{parameter_name}/history")
async def get_parameter_history(
    patient_id: str,
    parameter_name: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get historical values for a specific parameter"""
    history = parameter_extractor.get_parameter_history(
        db=db,
        patient_id=patient_id,
        parameter_name=parameter_name,
        limit=limit
    )
    
    return {
        "patient_id": patient_id,
        "parameter_name": parameter_name,
        "history": [
            {
                "value": p.value,
                "unit": p.unit,
                "timestamp": p.timestamp.isoformat(),
                "source": p.source.value,
                "source_id": p.source_id
            }
            for p in history
        ]
    }


@router.get("/stats/parameters/{patient_id}")
async def get_parameter_stats(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get parameter statistics for a patient"""
    all_params = db.query(Parameter).filter(Parameter.patient_id == patient_id).all()
    
    # Count by source
    by_source = {}
    for param in all_params:
        source = param.source.value
        by_source[source] = by_source.get(source, 0) + 1
    
    # Count unique parameters
    unique_params = set(p.parameter_name for p in all_params)
    
    # Get date range
    if all_params:
        earliest = min(p.timestamp for p in all_params)
        latest = max(p.timestamp for p in all_params)
    else:
        earliest = None
        latest = None
    
    return {
        "patient_id": patient_id,
        "total_parameters": len(all_params),
        "unique_parameters": len(unique_params),
        "by_source": by_source,
        "date_range": {
            "earliest": earliest.isoformat() if earliest else None,
            "latest": latest.isoformat() if latest else None
        }
    }
