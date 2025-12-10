from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import time
from sqlalchemy.orm import Session
from app.models.sql_models import ModelResult, Patient
from app.services.parameter_extractor import parameter_extractor
import logging
logger = logging.getLogger(__name__)
class DiseaseModel:
    """Base class for disease prediction models"""
    
    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
    
    def get_required_parameters(self) -> List[str]:
        """Return list of required parameter names"""
        raise NotImplementedError
    
    def run(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """
        Run the model with given parameters
        
        Args:
            parameters: Dictionary of parameter values
            
        Returns:
            Dictionary with model results
        """
        raise NotImplementedError
class AlzheimerRiskModel(DiseaseModel):
    """Alzheimer's disease risk prediction model"""
    
    def __init__(self):
        super().__init__(name="alzheimer_risk", version="1.0")
    
    def get_required_parameters(self) -> List[str]:
        return [
            "age",
            "mmse",  # Mini-Mental State Examination score
            "apoe4_status",  # APOE4 gene status (0, 1, or 2 alleles)
            "education_years",
            "hippocampal_volume",  # From MRI
            "amyloid_beta",  # From CSF or PET
        ]
    
    def run(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate Alzheimer's risk score
        
        This is a simplified model for demonstration.
        In production, use validated clinical models.
        """
        # Normalize MMSE score (0-30 scale, lower is worse)
        mmse_score = parameters.get("mmse", 30)
        mmse_risk = max(0, (30 - mmse_score) / 30)  # 0-1 scale
        
        # Age risk (increases with age)
        age = parameters.get("age", 65)
        age_risk = min(1, max(0, (age - 50) / 40))  # 0-1 scale
        
        # APOE4 risk
        apoe4 = parameters.get("apoe4_status", 0)
        apoe4_risk = apoe4 * 0.3  # Each allele adds 30% risk
        
        # Education protective factor
        education = parameters.get("education_years", 12)
        education_factor = max(0, 1 - (education / 20))
        
        # Hippocampal volume (smaller = higher risk)
        hippocampal_volume = parameters.get("hippocampal_volume", 3500)
        hippocampal_risk = max(0, (4000 - hippocampal_volume) / 1500)
        
        # Amyloid beta (higher = higher risk)
        amyloid = parameters.get("amyloid_beta", 200)
        amyloid_risk = min(1, amyloid / 500)
        
        # Weighted risk score
        risk_score = (
            mmse_risk * 0.25 +
            age_risk * 0.15 +
            apoe4_risk * 0.20 +
            education_factor * 0.10 +
            hippocampal_risk * 0.15 +
            amyloid_risk * 0.15
        )
        
        # Classify risk level
        if risk_score < 0.3:
            risk_level = "Low"
        elif risk_score < 0.6:
            risk_level = "Moderate"
        else:
            risk_level = "High"
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_percentage": round(risk_score * 100, 1),
            "contributing_factors": {
                "cognitive_decline": round(mmse_risk, 3),
                "age_factor": round(age_risk, 3),
                "genetic_risk": round(apoe4_risk, 3),
                "education_protection": round(1 - education_factor, 3),
                "brain_atrophy": round(hippocampal_risk, 3),
                "biomarker_risk": round(amyloid_risk, 3)
            },
            "recommendations": self._get_recommendations(risk_level)
        }
    
    def _get_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        if risk_level == "Low":
            return [
                "Continue regular cognitive activities",
                "Maintain healthy lifestyle",
                "Annual cognitive screening recommended"
            ]
        elif risk_level == "Moderate":
            return [
                "Increase cognitive stimulation activities",
                "Consider memory clinic evaluation",
                "Monitor cognitive function every 6 months",
                "Optimize cardiovascular health"
            ]
        else:
            return [
                "Urgent referral to memory clinic",
                "Comprehensive neuropsychological evaluation",
                "Consider clinical trial enrollment",
                "Discuss treatment options with specialist",
                "Quarterly cognitive monitoring"
            ]
class DiabetesRiskModel(DiseaseModel):
    """Type 2 Diabetes risk prediction model"""
    
    def __init__(self):
        super().__init__(name="diabetes_risk", version="1.0")
    
    def get_required_parameters(self) -> List[str]:
        return [
            "age",
            "bmi",
            "glucose",  # Fasting glucose
            "hba1c",
            "systolic_bp",
            "family_history_diabetes"  # 0 or 1
        ]
    
    def run(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """Calculate diabetes risk score"""
        # Age risk
        age = parameters.get("age", 45)
        age_risk = min(1, max(0, (age - 30) / 50))
        
        # BMI risk
        bmi = parameters.get("bmi", 25)
        if bmi < 25:
            bmi_risk = 0
        elif bmi < 30:
            bmi_risk = 0.3
        else:
            bmi_risk = min(1, 0.3 + (bmi - 30) / 20)
        
        # Glucose risk
        glucose = parameters.get("glucose", 100)
        glucose_risk = min(1, max(0, (glucose - 100) / 100))
        
        # HbA1c risk
        hba1c = parameters.get("hba1c", 5.5)
        hba1c_risk = min(1, max(0, (hba1c - 5.7) / 3))
        
        # Blood pressure risk
        systolic = parameters.get("systolic_bp", 120)
        bp_risk = min(1, max(0, (systolic - 120) / 60))
        
        # Family history
        family_history = parameters.get("family_history_diabetes", 0)
        
        # Calculate risk score
        risk_score = (
            age_risk * 0.15 +
            bmi_risk * 0.25 +
            glucose_risk * 0.25 +
            hba1c_risk * 0.20 +
            bp_risk * 0.10 +
            family_history * 0.05
        )
        
        # Classify
        if risk_score < 0.3:
            risk_level = "Low"
        elif risk_score < 0.6:
            risk_level = "Moderate"
        else:
            risk_level = "High"
        
        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_percentage": round(risk_score * 100, 1),
            "contributing_factors": {
                "age_factor": round(age_risk, 3),
                "obesity_factor": round(bmi_risk, 3),
                "glucose_level": round(glucose_risk, 3),
                "hba1c_level": round(hba1c_risk, 3),
                "blood_pressure": round(bp_risk, 3),
                "genetic_factor": family_history
            },
            "recommendations": self._get_recommendations(risk_level, parameters)
        }
    
    def _get_recommendations(self, risk_level: str, parameters: Dict[str, float]) -> List[str]:
        recommendations = []
        
        if risk_level == "High":
            recommendations.append("Consult endocrinologist immediately")
            recommendations.append("Start intensive lifestyle modification program")
        
        bmi = parameters.get("bmi", 25)
        if bmi >= 30:
            recommendations.append("Weight loss program recommended (target: 5-10% reduction)")
        
        glucose = parameters.get("glucose", 100)
        if glucose >= 126:
            recommendations.append("Diabetes diagnosis - start treatment")
        elif glucose >= 100:
            recommendations.append("Prediabetes - increase physical activity")
        
        recommendations.append("Monitor blood glucose regularly")
        recommendations.append("Maintain healthy diet (low glycemic index)")
        
        return recommendations
class ModelRunner:
    """Service for running disease prediction models"""
    
    def __init__(self):
        # Registry of available models
        self.models: Dict[str, DiseaseModel] = {
            "alzheimer_risk": AlzheimerRiskModel(),
            "diabetes_risk": DiabetesRiskModel(),
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a model"""
        model = self.models.get(model_name)
        if not model:
            return None
        
        return {
            "name": model.name,
            "version": model.version,
            "required_parameters": model.get_required_parameters()
        }
    
    async def run_model(
        self,
        db: Session,
        patient_id: str,
        model_name: str,
        override_parameters: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Run a disease model for a patient
        
        Args:
            db: Database session
            patient_id: Patient ID
            model_name: Name of model to run
            override_parameters: Optional parameter overrides
            
        Returns:
            Dictionary with model results and metadata
        """
        # Get model
        model = self.models.get(model_name)
        if not model:
            raise ValueError(f"Model '{model_name}' not found")
        
        # Get patient
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            raise ValueError(f"Patient '{patient_id}' not found")
        
        # Get required parameters
        required_params = model.get_required_parameters()
        logger.info(f"Model {model_name} requires: {required_params}")
        
        # Fetch parameters
        parameters = await parameter_extractor.get_parameters(
            db=db,
            patient_id=patient_id,
            parameter_names=required_params,
            fhir_id=patient.fhir_id
        )
        
        # Apply overrides
        if override_parameters:
            parameters.update(override_parameters)
        
        # Check for missing parameters
        missing = [p for p in required_params if p not in parameters]
        
        # Run model
        start_time = time.time()
        
        if missing:
            logger.warning(f"Missing parameters for model {model_name}: {missing}")
            results = {
                "error": "Missing required parameters",
                "missing_parameters": missing,
                "available_parameters": list(parameters.keys())
            }
            execution_time = int((time.time() - start_time) * 1000)
        else:
            results = model.run(parameters)
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Model {model_name} completed in {execution_time}ms")
        
        # Store result
        model_result = ModelResult(
            patient_id=patient_id,
            model_name=model_name,
            model_version=model.version,
            input_parameters=json.dumps(parameters),
            output_results=json.dumps(results),
            execution_time_ms=execution_time,
            confidence_score=results.get("risk_score") if not missing else None
        )
        
        db.add(model_result)
        db.commit()
        db.refresh(model_result)
        
        return {
            "result_id": model_result.id,
            "model_name": model_name,
            "model_version": model.version,
            "patient_id": patient_id,
            "input_parameters": parameters,
            "results": results,
            "missing_parameters": missing,
            "execution_time_ms": execution_time,
            "executed_at": model_result.executed_at
        }
    
    def get_model_history(
        self,
        db: Session,
        patient_id: str,
        model_name: Optional[str] = None,
        limit: int = 10
    ) -> List[ModelResult]:
        """Get model execution history for a patient"""
        query = db.query(ModelResult).filter(ModelResult.patient_id == patient_id)
        
        if model_name:
            query = query.filter(ModelResult.model_name == model_name)
        
        return query.order_by(ModelResult.executed_at.desc()).limit(limit).all()
# Create global model runner instance
model_runner = ModelRunner()
