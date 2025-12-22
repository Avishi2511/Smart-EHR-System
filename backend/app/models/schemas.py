"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================================
# Patient Schemas
# ============================================================================

class PatientCreate(BaseModel):
    fhir_id: str
    nfc_card_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    fhir_id: str
    nfc_card_id: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[datetime]
    gender: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    total_files: int = 0
    total_parameters: int = 0
    total_model_results: int = 0

    class Config:
        from_attributes = True


class PatientUpdate(BaseModel):
    nfc_card_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class PatientDetailResponse(PatientResponse):
    fhir_data: Optional[Dict[str, Any]] = None
    total_files: int = 0
    total_parameters: int = 0
    total_model_runs: int = 0


# ============================================================================
# Model Execution Schemas
# ============================================================================

class ModelExecutionRequest(BaseModel):
    patient_id: str
    model_name: str
    override_parameters: Optional[Dict[str, float]] = None


class ModelExecutionResponse(BaseModel):
    result_id: str
    model_name: str
    patient_id: str
    results: Dict[str, Any]
    missing_parameters: List[str] = []
    extracted_parameters: List[str] = []


class ModelResultResponse(BaseModel):
    id: str
    patient_id: str
    model_name: str
    model_version: Optional[str]
    input_parameters: Dict[str, Any]
    output_results: Dict[str, Any]
    execution_time_ms: Optional[int]
    confidence_score: Optional[float]
    executed_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ADNI Timeline Schemas
# ============================================================================

class TimelinePoint(BaseModel):
    """Single point on the disease progression timeline"""
    visit: str = Field(..., description="Visit code (e.g., 'bl', 'm06', 'm12')")
    months_from_baseline: int = Field(..., description="Months since baseline visit")
    is_historical: bool = Field(..., description="True if this is historical data")
    is_predicted: bool = Field(..., description="True if this is a prediction")
    scores: Dict[str, Optional[float]] = Field(..., description="Clinical scores at this timepoint")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score for this prediction")


class ADNIProgressionSummary(BaseModel):
    """Summary statistics for ADNI progression prediction"""
    baseline_scores: Dict[str, float]
    predicted_final_scores: Dict[str, float]
    predicted_changes: Dict[str, float]
    risk_level: str = Field(..., description="Overall risk level: Stable, Mild Decline, Moderate Decline, Severe Decline")
    prediction_horizon_months: int


class ADNIProgressionResponse(BaseModel):
    """Complete ADNI progression prediction response"""
    result_id: str
    model_name: str = "adni_progression"
    patient_id: str
    timeline: List[TimelinePoint]
    summary: ADNIProgressionSummary
    confidence_score: float
    metadata: Dict[str, Any]
    executed_at: datetime


# ============================================================================
# File Schemas
# ============================================================================

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_type: str
    category: str
    file_size: int
    uploaded_at: datetime
    processed: bool


class FileResponse(BaseModel):
    id: str
    patient_id: str
    filename: str
    file_type: str
    category: str
    file_path: str
    file_size: int
    processed: bool
    processing_error: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Query Schemas
# ============================================================================

class NaturalLanguageQueryRequest(BaseModel):
    patient_id: str
    query: str
    top_k: int = 5


class NaturalLanguageQueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float


class ParameterQueryRequest(BaseModel):
    patient_id: str
    parameter_names: List[str]


class ParameterQueryResponse(BaseModel):
    patient_id: str
    parameters: Dict[str, Any]
    sources: Dict[str, str]


# ============================================================================
# Query Schemas
# ============================================================================

class NaturalLanguageQueryRequest(BaseModel):
    patient_id: str
    query: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[str] = []
    confidence: float = 0.0


class ParameterQueryRequest(BaseModel):
    patient_id: str
    parameter_names: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ParameterResponse(BaseModel):
    id: str
    patient_id: str
    parameter_name: str
    value: float
    unit: Optional[str]
    source: str
    source_id: Optional[str]
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ParameterQueryResponse(BaseModel):
    patient_id: str
    parameters: List[ParameterResponse]


class RAGSearchResult(BaseModel):
    chunk_text: str
    file_id: str
    similarity_score: float
    metadata: Dict[str, Any] = {}


class RAGSearchRequest(BaseModel):
    patient_id: str
    query: str
    top_k: int = 5


class RAGSearchResponse(BaseModel):
    query: str
    results: List[RAGSearchResult]


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database_connected: bool
    vector_db_initialized: bool
    fhir_server_reachable: bool


# ============================================================================
# Observation Schemas
# ============================================================================

class ObservationResponse(BaseModel):
    id: str
    patient_id: str
    observation_type: str
    value: Optional[str]
    unit: Optional[str]
    effective_datetime: datetime
    doctor_remarks: Optional[str]
    medication_prescribed: Optional[str]
    document_link: Optional[str]
    status: str
    
    class Config:
        from_attributes = True


class ObservationFilterRequest(BaseModel):
    limit: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    observation_type: Optional[str] = None


class ObservationListResponse(BaseModel):
    observations: List[ObservationResponse]
    total: int
    filtered: int
