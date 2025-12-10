from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.sql_models import Parameter, DataSource
from app.models.schemas import (
    NaturalLanguageQuery,
    QueryResponse,
    ParameterQueryRequest,
    ParameterQueryResponse,
    ParameterResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult
)
from app.services.rag_service import rag_service
from app.services.parameter_extractor import parameter_extractor
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queries", tags=["Queries"])


@router.post("/natural-language", response_model=QueryResponse)
async def natural_language_query(
    query: NaturalLanguageQuery,
    db: Session = Depends(get_db)
):
    """
    Answer a natural language query about a patient
    
    Uses RAG to search patient documents and return relevant information.
    Example: "What was the patient's MMSE score last year?"
    """
    try:
        result = await rag_service.answer_query(
            query=query.query,
            patient_id=query.patient_id
        )
        
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"]
        )
        
    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing query"
        )


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


@router.post("/rag/search", response_model=RAGSearchResponse)
async def rag_search(
    request: RAGSearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic search on patient documents
    
    Returns relevant document chunks based on similarity to query.
    """
    try:
        results = await rag_service.search_documents(
            query=request.query,
            patient_id=request.patient_id,
            top_k=request.top_k
        )
        
        search_results = [
            RAGSearchResult(
                chunk_text=r["text"],
                file_id=r["file_id"],
                similarity_score=r["similarity_score"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]
        
        return RAGSearchResponse(
            query=request.query,
            results=search_results
        )
        
    except Exception as e:
        logger.error(f"Error performing RAG search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error performing search"
        )


@router.post("/parameters/extract/{patient_id}/{parameter_name}")
async def extract_parameter(
    patient_id: str,
    parameter_name: str,
    db: Session = Depends(get_db)
):
    """
    Extract a specific parameter value from patient documents using RAG
    
    Attempts to find and extract the parameter value from unstructured documents.
    If found, stores it in the SQL database for future use.
    """
    try:
        result = await rag_service.extract_parameter_value(
            parameter_name=parameter_name,
            patient_id=patient_id
        )
        
        if result is None:
            return {
                "patient_id": patient_id,
                "parameter_name": parameter_name,
                "found": False,
                "message": "Parameter not found in documents"
            }
        
        value, source_text, confidence = result
        
        # Store in database
        await parameter_extractor.store_manual_parameter(
            db=db,
            patient_id=patient_id,
            parameter_name=parameter_name,
            value=value
        )
        
        return {
            "patient_id": patient_id,
            "parameter_name": parameter_name,
            "found": True,
            "value": value,
            "source_text": source_text[:200] + "..." if len(source_text) > 200 else source_text,
            "confidence": confidence,
            "message": "Parameter extracted and stored successfully"
        }
        
    except Exception as e:
        logger.error(f"Error extracting parameter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error extracting parameter"
        )


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


@router.get("/vector-db/stats")
async def get_vector_db_stats():
    """Get vector database statistics"""
    from app.services.vector_db import vector_db
    
    stats = vector_db.get_stats()
    
    return {
        "vector_database": stats,
        "status": "initialized" if vector_db.is_initialized() else "not_initialized"
    }
