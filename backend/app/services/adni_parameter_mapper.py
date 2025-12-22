"""
ADNI Parameter Mapper

Maps backend parameters (from SQL/FHIR/RAG) to ADNI model input format.
Handles parameter extraction and formatting for the 193-dimensional input.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.parameter_extractor import parameter_extractor
from app.services.fhir_service import fhir_service

logger = logging.getLogger(__name__)


class ADNIParameterMapper:
    """Maps backend parameters to ADNI model format"""
    
    # Required parameters for ADNI model
    REQUIRED_PARAMS = [
        "age", "gender", "education", "apoe4",
        "mmse", "cdr_global", "cdr_sob", "adas_totscore"
    ]
    
    # Optional imaging parameters
    IMAGING_PARAMS = ["mri_rois", "pet_rois"]
    
    async def get_adni_parameters(
        self,
        patient_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Extract all required parameters for ADNI model
        
        Args:
            patient_id: Patient ID
            db: Database session
        
        Returns:
            Dictionary with demographics, clinical_scores, imaging, and historical_visits
        """
        try:
            # Get demographics
            demographics = await self._get_demographics(patient_id, db)
            
            # Get clinical scores
            clinical_scores = await self._get_clinical_scores(patient_id, db)
            
            # Get imaging features (placeholder for now)
            imaging = await self._get_imaging_features(patient_id, db)
            
            # Get historical visits (if available)
            historical_visits = await self._get_historical_visits(patient_id, db)
            
            return {
                "demographics": demographics,
                "clinical_scores": clinical_scores,
                "imaging": imaging,
                "historical_visits": historical_visits
            }
        
        except Exception as e:
            logger.error(f"Error extracting ADNI parameters for patient {patient_id}: {e}")
            raise
    
    async def _get_demographics(
        self,
        patient_id: str,
        db: Session
    ) -> Dict[str, float]:
        """Extract demographic parameters"""
        demographics = {}
        
        # Age
        age_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="age",
            db=db
        )
        demographics["age"] = age_result["value"] if age_result else 65.0  # Default
        
        # Gender (0=Female, 1=Male)
        gender_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="gender",
            db=db
        )
        if gender_result:
            # Convert to binary
            gender_str = str(gender_result.get("value", "")).lower()
            demographics["gender"] = 1.0 if gender_str in ["male", "m", "1"] else 0.0
        else:
            demographics["gender"] = 0.5  # Unknown
        
        # Education years
        education_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="education",
            db=db
        )
        demographics["education"] = education_result["value"] if education_result else 15.0  # Median
        
        # APOE4 allele count (0, 1, or 2)
        apoe4_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="apoe4",
            db=db
        )
        demographics["apoe4"] = apoe4_result["value"] if apoe4_result else 0.0  # Most common
        
        logger.info(f"Extracted demographics for patient {patient_id}: {demographics}")
        return demographics
    
    async def _get_clinical_scores(
        self,
        patient_id: str,
        db: Session
    ) -> Dict[str, Optional[float]]:
        """Extract clinical score parameters"""
        clinical_scores = {}
        
        # MMSE (0-30)
        mmse_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="mmse",
            db=db
        )
        clinical_scores["mmse"] = mmse_result["value"] if mmse_result else None
        
        # CDR Global (0-3)
        cdr_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="cdr_global",
            db=db
        )
        clinical_scores["cdr_global"] = cdr_result["value"] if cdr_result else None
        
        # CDR Sum of Boxes (0-18)
        cdr_sob_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="cdr_sob",
            db=db
        )
        clinical_scores["cdr_sob"] = cdr_sob_result["value"] if cdr_sob_result else None
        
        # ADAS Total Score (0-70)
        adas_result = await parameter_extractor.get_parameter(
            patient_id=patient_id,
            parameter_name="adas_totscore",
            db=db
        )
        clinical_scores["adas"] = adas_result["value"] if adas_result else None
        
        logger.info(f"Extracted clinical scores for patient {patient_id}: {clinical_scores}")
        return clinical_scores
    
    async def _get_imaging_features(
        self,
        patient_id: str,
        db: Session
    ) -> Dict[str, Optional[List[float]]]:
        """
        Get imaging features (MRI/PET ROIs)
        
        For MVP: Returns None (will use placeholder values)
        For production: Would query imaging_features table
        """
        # TODO: Implement ROI feature extraction/retrieval
        # For now, return None to use placeholder values
        
        return {
            "mri_rois": None,  # Will use placeholder (zeros with mask=0)
            "pet_rois": None   # Will use placeholder (zeros with mask=0)
        }
    
    async def _get_historical_visits(
        self,
        patient_id: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Get historical visit data for longitudinal modeling
        
        Returns list of visits with demographics, scores, and imaging at each timepoint
        """
        # For MVP: Return empty list (will use single baseline visit)
        # For production: Query parameters table for historical data
        
        # TODO: Implement historical visit retrieval
        # Query parameters table grouped by timestamp
        # Build visit records with all available data
        
        return []
    
    def format_for_model(
        self,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Format extracted parameters for ADNI model input
        
        Args:
            parameters: Output from get_adni_parameters()
        
        Returns:
            Formatted dictionary ready for ADNIModelService
        """
        return {
            "mri_rois": parameters["imaging"]["mri_rois"],
            "pet_rois": parameters["imaging"]["pet_rois"],
            "demographics": parameters["demographics"],
            "clinical_scores": parameters["clinical_scores"],
            "historical_visits": parameters["historical_visits"]
        }


# Global instance
adni_parameter_mapper = ADNIParameterMapper()
