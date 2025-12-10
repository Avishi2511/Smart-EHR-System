from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.database import get_db
from app.models.sql_models import ModelResult
from app.models.schemas import (
    ModelExecutionRequest,
    ModelExecutionResponse,
    ModelResultResponse
)
from app.services.model_runner import model_runner
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("/available")
async def get_available_models():
    """Get list of available disease models"""
    models = model_runner.get_available_models()
    
    model_info = []
    for model_name in models:
        info = model_runner.get_model_info(model_name)
        if info:
            model_info.append(info)
    
    return {
        "models": model_info,
        "count": len(model_info)
    }


@router.get("/{model_name}/info")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    info = model_runner.get_model_info(model_name)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found"
        )
    
    return info


@router.post("/execute", response_model=ModelExecutionResponse)
async def execute_model(
    request: ModelExecutionRequest,
    db: Session = Depends(get_db)
):
    """
    Execute a disease model for a patient
    
    The model will automatically fetch required parameters from:
    1. SQL database
    2. FHIR server
    3. RAG extraction from documents
    
    Missing parameters will be reported in the response.
    """
    try:
        result = await model_runner.run_model(
            db=db,
            patient_id=request.patient_id,
            model_name=request.model_name,
            override_parameters=request.override_parameters
        )
        
        # Extract information for response
        missing_params = result.get("missing_parameters", [])
        
        # Determine which parameters were extracted from RAG
        input_params = result.get("input_parameters", {})
        extracted_params = []
        
        # This is a simplified check - in production, track parameter sources
        if not missing_params and input_params:
            # Parameters were found somehow
            extracted_params = []
        
        return ModelExecutionResponse(
            result_id=result["result_id"],
            model_name=result["model_name"],
            patient_id=result["patient_id"],
            results=result["results"],
            missing_parameters=missing_params,
            extracted_parameters=extracted_params
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error executing model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error executing model"
        )


@router.get("/results/{result_id}", response_model=ModelResultResponse)
async def get_model_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific model result"""
    result = db.query(ModelResult).filter(ModelResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model result {result_id} not found"
        )
    
    return ModelResultResponse(
        id=result.id,
        patient_id=result.patient_id,
        model_name=result.model_name,
        model_version=result.model_version,
        input_parameters=json.loads(result.input_parameters),
        output_results=json.loads(result.output_results),
        execution_time_ms=result.execution_time_ms,
        confidence_score=result.confidence_score,
        executed_at=result.executed_at
    )


@router.get("/results/patient/{patient_id}", response_model=List[ModelResultResponse])
async def get_patient_model_results(
    patient_id: str,
    model_name: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get model execution history for a patient"""
    results = model_runner.get_model_history(
        db=db,
        patient_id=patient_id,
        model_name=model_name,
        limit=limit
    )
    
    return [
        ModelResultResponse(
            id=r.id,
            patient_id=r.patient_id,
            model_name=r.model_name,
            model_version=r.model_version,
            input_parameters=json.loads(r.input_parameters),
            output_results=json.loads(r.output_results),
            execution_time_ms=r.execution_time_ms,
            confidence_score=r.confidence_score,
            executed_at=r.executed_at
        )
        for r in results
    ]


@router.delete("/results/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model_result(
    result_id: str,
    db: Session = Depends(get_db)
):
    """Delete a model result"""
    result = db.query(ModelResult).filter(ModelResult.id == result_id).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model result {result_id} not found"
        )
    
    db.delete(result)
    db.commit()
    
    logger.info(f"Deleted model result {result_id}")


@router.get("/stats/patient/{patient_id}")
async def get_patient_model_stats(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get model execution statistics for a patient"""
    total_runs = db.query(ModelResult).filter(ModelResult.patient_id == patient_id).count()
    
    # Get runs by model
    results = db.query(ModelResult).filter(ModelResult.patient_id == patient_id).all()
    
    by_model = {}
    for result in results:
        model_name = result.model_name
        if model_name not in by_model:
            by_model[model_name] = {
                "count": 0,
                "latest_run": None
            }
        
        by_model[model_name]["count"] += 1
        
        if (by_model[model_name]["latest_run"] is None or 
            result.executed_at > by_model[model_name]["latest_run"]):
            by_model[model_name]["latest_run"] = result.executed_at.isoformat()
    
    return {
        "patient_id": patient_id,
        "total_model_runs": total_runs,
        "by_model": by_model
    }
