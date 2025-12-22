from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid
import enum
class FileType(str, enum.Enum):
    """Enum for file types"""
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    NOTE = "note"
    OTHER = "other"
class FileCategory(str, enum.Enum):
    """Enum for file categories"""
    LAB_REPORT = "lab_report"
    IMAGING = "imaging"
    CLINICAL_NOTE = "clinical_note"
    PRESCRIPTION = "prescription"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSENT_FORM = "consent_form"
    OTHER = "other"
class DataSource(str, enum.Enum):
    """Enum for data sources"""
    FHIR = "fhir"
    FILE = "file"
    MANUAL = "manual"
class Patient(Base):
    """Patient table - stores patient demographics and links to FHIR"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fhir_id = Column(String, unique=True, nullable=False, index=True)
    nfc_card_id = Column(String, unique=True, nullable=True, index=True)
    
    # Demographics (cached from FHIR)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    files = relationship("File", back_populates="patient", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="patient", cascade="all, delete-orphan")
    model_results = relationship("ModelResult", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(id='{self.id}', fhir_id='{self.fhir_id}', name='{self.first_name} {self.last_name}')>"
class File(Base):
    """File table - stores metadata of uploaded documents"""
    __tablename__ = "files"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    
    # File metadata
    filename = Column(String, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    category = Column(Enum(FileCategory), nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="files")
    
    def __repr__(self):
        return f"<File(id='{self.id}', filename='{self.filename}', patient_id='{self.patient_id}')>"
class Parameter(Base):
    """Parameter table - stores clinically relevant structured data"""
    __tablename__ = "parameters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Parameter details
    parameter_name = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    
    # Context
    source = Column(Enum(DataSource), nullable=False, index=True)
    source_id = Column(String, nullable=True)  # FHIR resource ID or file ID
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="parameters")
    
    def __repr__(self):
        return f"<Parameter(id='{self.id}', name='{self.parameter_name}', value={self.value}, unit='{self.unit}')>"
class ModelResult(Base):
    """ModelResult table - stores disease model execution results"""
    __tablename__ = "model_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Model details
    model_name = Column(String, nullable=False, index=True)
    model_version = Column(String, nullable=True)
    
    # Input/Output (stored as JSON text)
    input_parameters = Column(Text, nullable=False)  # JSON string
    output_results = Column(Text, nullable=False)  # JSON string
    
    # Metadata
    execution_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="model_results")
    
    def __repr__(self):
        return f"<ModelResult(id='{self.id}', model='{self.model_name}', patient_id='{self.patient_id}')>"


class Observation(Base):
    """Observation table - stores detailed patient observations"""
    __tablename__ = "observations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Observation details
    observation_type = Column(String, nullable=False, index=True)  # glucose, hba1c, mri, etc.
    value = Column(String, nullable=True)  # measurement value
    unit = Column(String, nullable=True)  # measurement unit
    
    # Clinical context
    doctor_remarks = Column(Text, nullable=True)
    medication_prescribed = Column(Text, nullable=True)
    document_link = Column(String, nullable=True)  # link to imaging/document
    status = Column(String, nullable=False, default="final")  # final, preliminary, etc.
    
    # Timestamps
    effective_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="observations")
    
    def __repr__(self):
        return f"<Observation(id='{self.id}', type='{self.observation_type}', patient_id='{self.patient_id}')>"
