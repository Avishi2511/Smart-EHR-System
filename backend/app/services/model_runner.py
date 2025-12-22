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


class ADNIProgressionModel(DiseaseModel):
    """ADNI Alzheimer's Disease Progression Prediction Model"""
    
    def __init__(self):
        super().__init__(name="adni_progression", version="1.0")
        from app.services.adni_model_service import adni_service
        from app.services.adni_parameter_mapper import adni_parameter_mapper
        self.adni_service = adni_service
        self.adni_parameter_mapper = adni_parameter_mapper
        
        # Load model on initialization
        try:
            self.adni_service.load_model()
            logger.info("ADNI model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ADNI model: {e}")
    
    def get_required_parameters(self) -> List[str]:
        """ADNI model parameters (extracted automatically)"""
        return [
            "age", "gender", "education", "apoe4",
            "mmse", "cdr_global", "cdr_sob", "adas_totscore"
        ]
    
    async def run_async(self, patient_id: str, db: Session) -> Dict[str, Any]:
        """
        Run ADNI progression model (async version)
        
        This method extracts parameters and runs the full progression prediction
        """
        # Extract ADNI-specific parameters
        adni_params = await self.adni_parameter_mapper.get_adni_parameters(
            patient_id=patient_id,
            db=db
        )
        
        # Format for model
        model_input = self.adni_parameter_mapper.format_for_model(adni_params)
        
        # Run prediction
        predictions = self.adni_service.predict_progression(
            patient_data=model_input,
            num_future_points=5  # Predict 5 future visits (30 months)
        )
        
        # Format results for timeline
        timeline = self._format_timeline(predictions, adni_params)
        
        # Calculate summary statistics
        summary = self._calculate_summary(timeline)
        
        return {
            "timeline": timeline,
            "summary": summary,
            "predictions": predictions["predictions"],
            "timepoints": predictions["timepoints"],
            "confidence_score": predictions["confidence_score"],
            "metadata": predictions["metadata"]
        }
    
    def run(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        """
        Synchronous run method (required by base class)
        
        Note: ADNI model should use run_async() for full functionality
        """
        # This is a simplified version for compatibility
        # Real usage should call run_async()
        return {
            "message": "ADNI model requires async execution. Use run_async() instead.",
            "parameters_received": list(parameters.keys())
        }
    
    def _format_timeline(
        self, 
        predictions: Dict[str, Any],
        adni_params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format predictions as timeline points"""
        timeline = []
        
        # Historical points
        hist_timepoints = predictions["timepoints"]["historical"]
        for i, visit in enumerate(hist_timepoints):
            timeline.append({
                "visit": visit,
                "months_from_baseline": self._visit_to_months(visit),
                "is_historical": True,
                "is_predicted": False,
                "scores": {
                    "mmse": predictions["predictions"]["mmse"]["historical"][i],
                    "cdr_global": predictions["predictions"]["cdr_global"]["historical"][i],
                    "cdr_sob": predictions["predictions"]["cdr_sob"]["historical"][i],
                    "adas_totscore": predictions["predictions"]["adas_totscore"]["historical"][i]
                },
                "confidence": 1.0  # Historical data has full confidence
            })
        
        # Future predictions
        future_timepoints = predictions["timepoints"]["future"]
        confidence = predictions["confidence_score"]
        
        for i, visit in enumerate(future_timepoints):
            timeline.append({
                "visit": visit,
                "months_from_baseline": self._visit_to_months(visit),
                "is_historical": False,
                "is_predicted": True,
                "scores": {
                    "mmse": predictions["predictions"]["mmse"]["future"][i],
                    "cdr_global": predictions["predictions"]["cdr_global"]["future"][i],
                    "cdr_sob": predictions["predictions"]["cdr_sob"]["future"][i],
                    "adas_totscore": predictions["predictions"]["adas_totscore"]["future"][i]
                },
                "confidence": confidence * (1 - i * 0.1)  # Decrease confidence over time
            })
        
        return timeline
    
    def _visit_to_months(self, visit: str) -> int:
        """Convert visit code to months from baseline"""
        visit_map = {
            "sc": -1, "bl": 0, "m03": 3, "m06": 6, "m12": 12, "m18": 18,
            "m24": 24, "m36": 36, "m48": 48, "m60": 60, "m72": 72,
            "m84": 84, "m96": 96, "m108": 108, "m120": 120
        }
        return visit_map.get(visit, 0)
    
    def _calculate_summary(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from timeline"""
        if not timeline:
            return {}
        
        # Get baseline and last prediction
        baseline = timeline[0]["scores"]
        last_prediction = timeline[-1]["scores"]
        
        # Calculate changes
        changes = {
            "mmse": last_prediction["mmse"] - baseline["mmse"],
            "cdr_global": last_prediction["cdr_global"] - baseline["cdr_global"],
            "cdr_sob": last_prediction["cdr_sob"] - baseline["cdr_sob"],
            "adas_totscore": last_prediction["adas_totscore"] - baseline["adas_totscore"]
        }
        
        # Determine risk level based on MMSE decline
        mmse_decline = -changes["mmse"]  # Negative change means decline
        if mmse_decline < 2:
            risk_level = "Stable"
        elif mmse_decline < 5:
            risk_level = "Mild Decline"
        elif mmse_decline < 10:
            risk_level = "Moderate Decline"
        else:
            risk_level = "Severe Decline"
        
        return {
            "baseline_scores": baseline,
            "predicted_final_scores": last_prediction,
            "predicted_changes": changes,
            "risk_level": risk_level,
            "prediction_horizon_months": timeline[-1]["months_from_baseline"]
        }


class ModelRunner:
    """Service for running disease prediction models"""
    
    def __init__(self):
        # Registry of available models
        self.models: Dict[str, DiseaseModel] = {
            "alzheimer_risk": AlzheimerRiskModel(),
            "diabetes_risk": DiabetesRiskModel(),
            "adni_progression": ADNIProgressionModel(),
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
        
        # Run model
        start_time = time.time()
        
        # Special handling for ADNI progression model
        if model_name == "adni_progression" and hasattr(model, 'run_async'):
            logger.info("Running ADNI progression model (async)")
            try:
                results = await model.run_async(patient_id=patient_id, db=db)
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"ADNI model completed in {execution_time}ms")
                
                # Extract parameters for storage
                parameters = {
                    "model_type": "progression",
                    "prediction_horizon_months": results.get("summary", {}).get("prediction_horizon_months", 30)
                }
                missing = []
                
            except Exception as e:
                logger.error(f"Error running ADNI model: {e}")
                results = {
                    "error": str(e),
                    "message": "ADNI model execution failed"
                }
                execution_time = int((time.time() - start_time) * 1000)
                parameters = {}
                missing = required_params
        else:
            # Standard model execution
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
