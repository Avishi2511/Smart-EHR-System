from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class FHIRResourceBuilder:
    """Build FHIR R4 compliant resources"""
    
    def __init__(self):
        # LOINC code mappings
        self.loinc_mapping = {
            "systolic_bp": {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg"},
            "diastolic_bp": {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg"},
            "heart_rate": {"code": "8867-4", "display": "Heart rate", "unit": "beats/min"},
            "respiratory_rate": {"code": "9279-1", "display": "Respiratory rate", "unit": "breaths/min"},
            "body_temperature": {"code": "8310-5", "display": "Body temperature", "unit": "Cel"},
            "body_weight": {"code": "29463-7", "display": "Body weight", "unit": "kg"},
            "body_height": {"code": "8302-2", "display": "Body height", "unit": "cm"},
            "bmi": {"code": "39156-5", "display": "Body mass index", "unit": "kg/m2"},
            "oxygen_saturation": {"code": "2708-6", "display": "Oxygen saturation", "unit": "%"},
            "glucose": {"code": "2339-0", "display": "Glucose", "unit": "mg/dL"},
            "cholesterol_total": {"code": "2093-3", "display": "Cholesterol total", "unit": "mg/dL"},
            "hdl_cholesterol": {"code": "2085-9", "display": "HDL Cholesterol", "unit": "mg/dL"},
            "ldl_cholesterol": {"code": "2089-1", "display": "LDL Cholesterol", "unit": "mg/dL"},
            "triglycerides": {"code": "2571-8", "display": "Triglycerides", "unit": "mg/dL"},
            "hba1c": {"code": "4548-4", "display": "Hemoglobin A1c", "unit": "%"},
            "hemoglobin": {"code": "718-7", "display": "Hemoglobin", "unit": "g/dL"},
            "wbc_count": {"code": "6690-2", "display": "White blood cell count", "unit": "10*3/uL"},
            "platelet_count": {"code": "777-3", "display": "Platelet count", "unit": "10*3/uL"},
            "creatinine": {"code": "2160-0", "display": "Creatinine", "unit": "mg/dL"},
            "bun": {"code": "3094-0", "display": "Blood urea nitrogen", "unit": "mg/dL"},
            "alt": {"code": "1742-6", "display": "Alanine aminotransferase", "unit": "U/L"},
            "ast": {"code": "1920-8", "display": "Aspartate aminotransferase", "unit": "U/L"},
        }
    
    def build_observation(
        self,
        observation_type: str,
        value: float,
        patient_id: str,
        effective_date: Optional[str] = None,
        unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a FHIR Observation resource
        
        Args:
            observation_type: Type of observation (e.g., "glucose", "systolic_bp")
            value: Numeric value
            patient_id: FHIR patient ID
            effective_date: Date of observation (ISO format)
            unit: Unit of measurement (optional, will use default if not provided)
            
        Returns:
            FHIR Observation resource as dict
        """
        if observation_type not in self.loinc_mapping:
            logger.warning(f"Unknown observation type: {observation_type}")
            # Fallback to text-based observation
            return self._build_text_observation(observation_type, value, patient_id, effective_date, unit)
        
        loinc_info = self.loinc_mapping[observation_type]
        obs_id = f"obs-{uuid.uuid4().hex[:8]}"
        
        observation = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc_info["code"],
                    "display": loinc_info["display"]
                }],
                "text": loinc_info["display"]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": effective_date or datetime.now().isoformat(),
            "valueQuantity": {
                "value": value,
                "unit": unit or loinc_info["unit"],
                "system": "http://unitsofmeasure.org",
                "code": unit or loinc_info["unit"]
            }
        }
        
        logger.info(f"Built Observation: {loinc_info['display']} = {value} {loinc_info['unit']}")
        return observation
    
    def _build_text_observation(
        self,
        observation_name: str,
        value: float,
        patient_id: str,
        effective_date: Optional[str] = None,
        unit: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build observation without LOINC code (text-based)"""
        obs_id = f"obs-{uuid.uuid4().hex[:8]}"
        
        observation = {
            "resourceType": "Observation",
            "id": obs_id,
            "status": "final",
            "code": {
                "text": observation_name
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": effective_date or datetime.now().isoformat(),
            "valueQuantity": {
                "value": value,
                "unit": unit or ""
            }
        }
        
        return observation
    
    def build_condition(
        self,
        code_text: str,
        patient_id: str,
        clinical_status: str = "active",
        onset_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a FHIR Condition resource
        
        Args:
            code_text: Condition name/description
            patient_id: FHIR patient ID
            clinical_status: Status (active, inactive, resolved)
            onset_date: Date of onset (ISO format)
            
        Returns:
            FHIR Condition resource as dict
        """
        condition_id = f"condition-{uuid.uuid4().hex[:8]}"
        
        condition = {
            "resourceType": "Condition",
            "id": condition_id,
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clinical_status
                }]
            },
            "code": {
                "text": code_text
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            }
        }
        
        if onset_date:
            condition["onsetDateTime"] = onset_date
        
        logger.info(f"Built Condition: {code_text} ({clinical_status})")
        return condition
    
    def build_medication_request(
        self,
        medication_text: str,
        patient_id: str,
        status: str = "active",
        dosage_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a FHIR MedicationRequest resource
        
        Args:
            medication_text: Medication name and dosage
            patient_id: FHIR patient ID
            status: Status (active, completed, stopped)
            dosage_instruction: Dosage instructions text
            
        Returns:
            FHIR MedicationRequest resource as dict
        """
        med_id = f"med-req-{uuid.uuid4().hex[:8]}"
        
        medication_request = {
            "resourceType": "MedicationRequest",
            "id": med_id,
            "status": status,
            "intent": "order",
            "medication": {
                "concept": {
                    "text": medication_text
                }
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            }
        }
        
        if dosage_instruction:
            medication_request["dosageInstruction"] = [{
                "text": dosage_instruction
            }]
        
        logger.info(f"Built MedicationRequest: {medication_text} ({status})")
        return medication_request


# Create global FHIR resource builder instance
fhir_resource_builder = FHIRResourceBuilder()
