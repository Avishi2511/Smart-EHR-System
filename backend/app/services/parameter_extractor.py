from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.sql_models import Parameter, DataSource
from app.services.fhir_service import fhir_service
import logging
logger = logging.getLogger(__name__)
class ParameterExtractor:
    """Service for extracting and managing clinical parameters"""
    
    async def get_parameters(
        self,
        db: Session,
        patient_id: str,
        parameter_names: List[str],
        fhir_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get parameter values from SQL or FHIR
        
        Priority order:
        1. SQL database (most recent values)
        2. FHIR server (if FHIR ID provided)
        
        Args:
            db: Database session
            patient_id: Patient ID
            parameter_names: List of parameter names to retrieve
            fhir_id: Optional FHIR patient ID
            
        Returns:
            Dictionary mapping parameter names to values
        """
        parameters = {}
        missing_params = []
        
        # Step 1: Check SQL database
        for param_name in parameter_names:
            sql_param = self._get_latest_from_sql(db, patient_id, param_name)
            if sql_param:
                parameters[param_name] = sql_param.value
                logger.info(f"Found {param_name} in SQL: {sql_param.value}")
            else:
                missing_params.append(param_name)
        
        if not missing_params:
            return parameters
        
        # Step 2: Try FHIR server if FHIR ID provided
        if fhir_id:
            fhir_params = await self._get_from_fhir(fhir_id, missing_params)
            
            for param_name, value in fhir_params.items():
                parameters[param_name] = value
                
                # Store in SQL for future use
                self._store_parameter(
                    db=db,
                    patient_id=patient_id,
                    parameter_name=param_name,
                    value=value,
                    source=DataSource.FHIR,
                    source_id=fhir_id
                )
                
                missing_params.remove(param_name)
                logger.info(f"Found {param_name} in FHIR: {value}")
        
        return parameters
    
    def _get_latest_from_sql(
        self,
        db: Session,
        patient_id: str,
        parameter_name: str
    ) -> Optional[Parameter]:
        """Get the most recent parameter value from SQL"""
        return db.query(Parameter)\
            .filter(
                Parameter.patient_id == patient_id,
                Parameter.parameter_name == parameter_name
            )\
            .order_by(Parameter.timestamp.desc())\
            .first()
    
    async def _get_from_fhir(
        self,
        fhir_id: str,
        parameter_names: List[str]
    ) -> Dict[str, float]:
        """Extract parameters from FHIR server"""
        parameters = {}
        
        # Get vital signs
        vital_signs = await fhir_service.extract_vital_signs(fhir_id)
        for param_name in parameter_names:
            if param_name in vital_signs:
                parameters[param_name] = vital_signs[param_name]
        
        # Get lab results
        lab_results = await fhir_service.extract_lab_results(fhir_id)
        for param_name in parameter_names:
            if param_name in lab_results:
                parameters[param_name] = lab_results[param_name]
        
        return parameters
    
    def _store_parameter(
        self,
        db: Session,
        patient_id: str,
        parameter_name: str,
        value: float,
        source: DataSource,
        source_id: Optional[str] = None,
        unit: Optional[str] = None
    ):
        """Store parameter in SQL database"""
        parameter = Parameter(
            patient_id=patient_id,
            parameter_name=parameter_name,
            value=value,
            unit=unit,
            source=source,
            source_id=source_id,
            timestamp=datetime.utcnow()
        )
        
        db.add(parameter)
        db.commit()
        logger.info(f"Stored parameter {parameter_name}={value} from {source.value}")
    
    async def store_manual_parameter(
        self,
        db: Session,
        patient_id: str,
        parameter_name: str,
        value: float,
        unit: Optional[str] = None
    ):
        """Store manually entered parameter"""
        self._store_parameter(
            db=db,
            patient_id=patient_id,
            parameter_name=parameter_name,
            value=value,
            source=DataSource.MANUAL,
            unit=unit
        )
    
    def get_parameter_history(
        self,
        db: Session,
        patient_id: str,
        parameter_name: str,
        limit: int = 10
    ) -> List[Parameter]:
        """Get parameter history for a patient"""
        return db.query(Parameter)\
            .filter(
                Parameter.patient_id == patient_id,
                Parameter.parameter_name == parameter_name
            )\
            .order_by(Parameter.timestamp.desc())\
            .limit(limit)\
            .all()
    
    def get_all_parameters(
        self,
        db: Session,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Parameter]:
        """Get all parameters for a patient within a date range"""
        query = db.query(Parameter).filter(Parameter.patient_id == patient_id)
        
        if start_date:
            query = query.filter(Parameter.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Parameter.timestamp <= end_date)
        
        return query.order_by(Parameter.timestamp.desc()).all()
    
    def get_latest_parameters(
        self,
        db: Session,
        patient_id: str
    ) -> Dict[str, Parameter]:
        """Get the most recent value for each parameter"""
        parameters = db.query(Parameter)\
            .filter(Parameter.patient_id == patient_id)\
            .order_by(Parameter.timestamp.desc())\
            .all()
        
        # Keep only the latest value for each parameter name
        latest = {}
        for param in parameters:
            if param.parameter_name not in latest:
                latest[param.parameter_name] = param
        
        return latest
    
    async def sync_from_fhir(
        self,
        db: Session,
        patient_id: str,
        fhir_id: str
    ) -> int:
        """
        Sync all available parameters from FHIR server
        
        Args:
            db: Database session
            patient_id: Patient ID
            fhir_id: FHIR patient ID
            
        Returns:
            Number of parameters synced
        """
        count = 0
        
        # Get vital signs
        vital_signs = await fhir_service.extract_vital_signs(fhir_id)
        for param_name, value in vital_signs.items():
            self._store_parameter(
                db=db,
                patient_id=patient_id,
                parameter_name=param_name,
                value=value,
                source=DataSource.FHIR,
                source_id=fhir_id
            )
            count += 1
        
        # Get lab results
        lab_results = await fhir_service.extract_lab_results(fhir_id)
        for param_name, value in lab_results.items():
            self._store_parameter(
                db=db,
                patient_id=patient_id,
                parameter_name=param_name,
                value=value,
                source=DataSource.FHIR,
                source_id=fhir_id
            )
            count += 1
        
        logger.info(f"Synced {count} parameters from FHIR for patient {patient_id}")
        return count
# Create global parameter extractor instance
parameter_extractor = ParameterExtractor()
