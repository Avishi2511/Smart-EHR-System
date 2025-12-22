"""
Alzheimer's Prediction API endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alzheimers", tags=["Alzheimer's Predictions"])


# Pydantic models for request/response
class CognitiveScores(BaseModel):
    MMSE: float
    CDR_Global: float
    CDR_SOB: float
    ADAS_Cog: float


class LastVisit(BaseModel):
    date: str
    scores: CognitiveScores


class FuturePrediction(BaseModel):
    months_ahead: int
    scores: CognitiveScores


class PredictionRequest(BaseModel):
    patient_id: str
    prediction_time: str
    last_visit: LastVisit
    future_predictions: List[FuturePrediction]


class PredictionResponse(BaseModel):
    success: bool
    message: str
    patient_id: str
    predictions_stored: int


# In-memory storage for predictions (replace with database in production)
predictions_store: Dict[str, PredictionRequest] = {}


@router.post("/predictions", response_model=PredictionResponse)
async def receive_predictions(prediction_data: PredictionRequest):
    """
    Receive Alzheimer's progression predictions from the Python pipeline.
    
    This endpoint stores the clinically constrained prediction scores
    for a patient and makes them available for frontend display.
    """
    try:
        patient_id = prediction_data.patient_id
        
        # Validate scores are within clinical ranges
        last_visit_scores = prediction_data.last_visit.scores
        
        # MMSE: 0-30
        if not (0 <= last_visit_scores.MMSE <= 30):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MMSE score: {last_visit_scores.MMSE} (must be 0-30)"
            )
        
        # CDR-Global: 0, 0.5, 1, 2, 3
        valid_cdr = {0, 0.5, 1, 2, 3}
        if last_visit_scores.CDR_Global not in valid_cdr:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CDR-Global: {last_visit_scores.CDR_Global} (must be in {valid_cdr})"
            )
        
        # CDR-SOB: 0-18
        if not (0 <= last_visit_scores.CDR_SOB <= 18):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CDR-SOB: {last_visit_scores.CDR_SOB} (must be 0-18)"
            )
        
        # ADAS-Cog: 0-70
        if not (0 <= last_visit_scores.ADAS_Cog <= 70):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ADAS-Cog: {last_visit_scores.ADAS_Cog} (must be 0-70)"
            )
        
        # Store predictions
        predictions_store[patient_id] = prediction_data
        
        logger.info(f"Stored predictions for patient {patient_id}")
        logger.info(f"  Last visit: {prediction_data.last_visit.date}")
        logger.info(f"  Future predictions: {len(prediction_data.future_predictions)}")
        
        return PredictionResponse(
            success=True,
            message="Predictions stored successfully",
            patient_id=patient_id,
            predictions_stored=len(prediction_data.future_predictions)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store predictions: {str(e)}"
        )


@router.get("/predictions/{patient_id}")
async def get_predictions(patient_id: str):
    """
    Retrieve stored predictions for a patient.
    """
    if patient_id not in predictions_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No predictions found for patient {patient_id}"
        )
    
    return predictions_store[patient_id]


@router.get("/predictions")
async def list_all_predictions():
    """
    List all stored predictions (for debugging).
    """
    return {
        "total_patients": len(predictions_store),
        "patients": list(predictions_store.keys())
    }


class RunPredictionRequest(BaseModel):
    patient_id: str


@router.post("/run-prediction")
async def run_prediction(request: RunPredictionRequest):
    """
    Read ADNI prediction results for a patient.
    
    Reads pre-generated prediction file from adni-python/api/predictions/
    """
    import json
    from pathlib import Path
    
    try:
        patient_id = request.patient_id
        logger.info(f"Reading predictions for patient: {patient_id}")
        
        # Path to prediction file
        adni_root = Path(__file__).parent.parent.parent.parent / "adni-python"
        predictions_file = adni_root / "api" / "predictions" / f"{patient_id}_predictions.json"
        
        if not predictions_file.exists():
            logger.error(f"Prediction file not found: {predictions_file}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No predictions found for patient {patient_id}"
            )
        
        # Read the prediction file
        with open(predictions_file, 'r', encoding='utf-8') as f:
            predictions_data = json.load(f)
        
        logger.info(f"Loaded {len(predictions_data.get('future_predictions', []))} predictions")
        
        # Get historical sessions
        historical_sessions = predictions_data.get("historical_sessions", [])
        if not historical_sessions:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No historical sessions found"
            )
        
        last_session = historical_sessions[-1]
        future_predictions = predictions_data.get("future_predictions", [])
        
        # Format response
        response = {
            "patient_id": patient_id,
            "prediction_time": predictions_data.get("prediction_timestamp", datetime.now().isoformat()),
            "last_visit": {
                "date": last_session["session_date"],
                "scores": {
                    "MMSE": last_session["predicted_scores"]["MMSE"],
                    "CDR_Global": last_session["predicted_scores"]["CDR_Global"],
                    "CDR_SOB": last_session["predicted_scores"]["CDR_SOB"],
                    "ADAS_Cog": last_session["predicted_scores"]["ADAS_Cog"]
                }
            },
            "future_predictions": [
                {
                    "months_from_last_visit": pred["months_from_last_visit"],
                    "predicted_scores": {
                        "MMSE": pred["predicted_scores"]["MMSE"],
                        "CDR_Global": pred["predicted_scores"]["CDR_Global"],
                        "CDR_SOB": pred["predicted_scores"]["CDR_SOB"],
                        "ADAS_Cog": pred["predicted_scores"]["ADAS_Cog"]
                    }
                }
                for pred in future_predictions
            ]
        }
        
        logger.info(f"Successfully loaded predictions for {patient_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read predictions: {str(e)}"
        )
