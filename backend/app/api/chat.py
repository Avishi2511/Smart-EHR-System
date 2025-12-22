from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models.sql_models import Patient
from app.services.query_processor import query_processor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatQueryRequest(BaseModel):
    """Request model for chat query"""
    patient_id: str  # FHIR patient ID
    query: str


class ChatQueryResponse(BaseModel):
    """Response model for chat query"""
    success: bool
    query: str
    query_type: str
    data: List[Dict[str, Any]]
    count: int
    error: Optional[str] = None
    time_period: Optional[Dict[str, Any]] = None



@router.post("/query", response_model=ChatQueryResponse)
async def process_chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Process a natural language query about patient data
    
    Examples:
    - "What was the patient's blood pressure in the last 3 months?"
    - "Show me the latest glucose readings"
    - "What medications is the patient taking?"
    """
    try:
        # Verify patient exists
        patient = db.query(Patient).filter(Patient.fhir_id == request.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient {request.patient_id} not found"
            )
        
        logger.info(f"Processing query for patient {request.patient_id}: {request.query}")
        
        # Parse the query
        parsed_query = query_processor.parse_query(request.query, request.patient_id)
        
        # Execute the query
        result = await query_processor.execute_query(parsed_query)
        
        if not result.get("success", False):
            return ChatQueryResponse(
                success=False,
                query=request.query,
                query_type="error",
                data=[],
                count=0,
                error=result.get("error", "Unknown error occurred")
            )
        
        return ChatQueryResponse(
            success=True,
            query=request.query,
            query_type=result.get("query_type", "general"),
            data=result.get("data", []),
            count=result.get("count", 0),
            time_period=result.get("time_period")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.get("/suggestions/{patient_id}")
async def get_query_suggestions(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get suggested queries for a patient
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.fhir_id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    suggestions = query_processor.get_suggested_queries(patient_id)
    
    return {
        "patient_id": patient_id,
        "suggestions": suggestions
    }
