import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.config import settings
import logging
logger = logging.getLogger(__name__)
class FHIRService:
    """Service for interacting with the FHIR server"""
    
    def __init__(self):
        self.base_url = settings.FHIR_SERVER_URL
        self.timeout = settings.FHIR_SERVER_TIMEOUT
    
    async def get_patient(self, fhir_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch patient resource from FHIR server
        
        Args:
            fhir_id: FHIR patient ID
            
        Returns:
            Patient resource dict or None if not found
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/Patient/{fhir_id}")
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"Patient {fhir_id} not found in FHIR server")
                    return None
                else:
                    logger.error(f"FHIR server error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching patient from FHIR: {e}")
            return None
    
    async def get_observations(
        self, 
        patient_id: str, 
        code: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch observations for a patient
        
        Args:
            patient_id: FHIR patient ID
            code: Optional LOINC/SNOMED code to filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of observation resources
        """
        try:
            params = {"patient": patient_id}
            
            if code:
                params["code"] = code
            
            if start_date:
                params["date"] = f"ge{start_date.isoformat()}"
            
            if end_date:
                date_param = params.get("date", "")
                if date_param:
                    params["date"] = f"{date_param}&le{end_date.isoformat()}"
                else:
                    params["date"] = f"le{end_date.isoformat()}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/Observation",
                    params=params
                )
                
                if response.status_code == 200:
                    bundle = response.json()
                    entries = bundle.get("entry", [])
                    return [entry.get("resource") for entry in entries]
                else:
                    logger.error(f"Error fetching observations: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching observations from FHIR: {e}")
            return []
    
    async def get_observations_by_code(
        self, 
        patient_id: str, 
        loinc_code: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch observations for a patient filtered by LOINC code
        
        This is an alias method for get_observations with code filter
        
        Args:
            patient_id: FHIR patient ID
            loinc_code: LOINC code to filter observations
            
        Returns:
            List of observation resources matching the code
        """
        # Get all observations for the patient (without code filter)
        all_observations = await self.get_observations(patient_id=patient_id)
        
        # Filter by LOINC code client-side
        filtered_observations = []
        for obs in all_observations:
            # Check if any coding in the observation matches the LOINC code
            codings = obs.get("code", {}).get("coding", [])
            for coding in codings:
                if coding.get("code") == loinc_code:
                    filtered_observations.append(obs)
                    break  # Found a match, no need to check other codings
        
        return filtered_observations
    
    async def get_conditions(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetch conditions for a patient
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            List of condition resources
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/Condition",
                    params={"patient": patient_id}
                )
                
                if response.status_code == 200:
                    bundle = response.json()
                    entries = bundle.get("entry", [])
                    return [entry.get("resource") for entry in entries]
                else:
                    logger.error(f"Error fetching conditions: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching conditions from FHIR: {e}")
            return []
    
    async def get_medication_requests(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Fetch medication requests for a patient
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            List of medication request resources
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/MedicationRequest",
                    params={"patient": patient_id}
                )
                
                if response.status_code == 200:
                    bundle = response.json()
                    entries = bundle.get("entry", [])
                    return [entry.get("resource") for entry in entries]
                else:
                    logger.error(f"Error fetching medication requests: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching medication requests from FHIR: {e}")
            return []
    
    async def extract_vital_signs(self, patient_id: str) -> Dict[str, float]:
        """
        Extract common vital signs from FHIR observations
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            Dictionary of vital sign parameters
        """
        observations = await self.get_observations(patient_id)
        vital_signs = {}
        
        # Common LOINC codes for vital signs
        loinc_mapping = {
            "8480-6": "systolic_bp",  # Systolic blood pressure
            "8462-4": "diastolic_bp",  # Diastolic blood pressure
            "8867-4": "heart_rate",  # Heart rate
            "9279-1": "respiratory_rate",  # Respiratory rate
            "8310-5": "body_temperature",  # Body temperature
            "29463-7": "body_weight",  # Body weight
            "8302-2": "body_height",  # Body height
            "39156-5": "bmi",  # Body mass index
            "2708-6": "oxygen_saturation",  # Oxygen saturation
        }
        
        for obs in observations:
            code = obs.get("code", {})
            coding = code.get("coding", [])
            
            for code_item in coding:
                loinc_code = code_item.get("code")
                if loinc_code in loinc_mapping:
                    value_quantity = obs.get("valueQuantity", {})
                    value = value_quantity.get("value")
                    
                    if value is not None:
                        param_name = loinc_mapping[loinc_code]
                        # Keep the most recent value
                        if param_name not in vital_signs:
                            vital_signs[param_name] = float(value)
        
        return vital_signs
    
    async def extract_lab_results(self, patient_id: str) -> Dict[str, float]:
        """
        Extract common lab results from FHIR observations
        
        Args:
            patient_id: FHIR patient ID
            
        Returns:
            Dictionary of lab result parameters
        """
        observations = await self.get_observations(patient_id)
        lab_results = {}
        
        # Common LOINC codes for lab results
        loinc_mapping = {
            "2339-0": "glucose",  # Glucose
            "2093-3": "cholesterol_total",  # Total cholesterol
            "2085-9": "hdl_cholesterol",  # HDL cholesterol
            "2089-1": "ldl_cholesterol",  # LDL cholesterol
            "2571-8": "triglycerides",  # Triglycerides
            "4548-4": "hba1c",  # Hemoglobin A1c
            "718-7": "hemoglobin",  # Hemoglobin
            "6690-2": "wbc_count",  # White blood cell count
            "777-3": "platelet_count",  # Platelet count
            "2160-0": "creatinine",  # Creatinine
            "3094-0": "bun",  # Blood urea nitrogen
            "1742-6": "alt",  # Alanine aminotransferase
            "1920-8": "ast",  # Aspartate aminotransferase
        }
        
        for obs in observations:
            code = obs.get("code", {})
            coding = code.get("coding", [])
            
            for code_item in coding:
                loinc_code = code_item.get("code")
                if loinc_code in loinc_mapping:
                    value_quantity = obs.get("valueQuantity", {})
                    value = value_quantity.get("value")
                    
                    if value is not None:
                        param_name = loinc_mapping[loinc_code]
                        if param_name not in lab_results:
                            lab_results[param_name] = float(value)
        
        return lab_results
    
    async def create_observation(self, observation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an Observation resource in FHIR server
        
        Args:
            observation_data: FHIR Observation resource dict
            
        Returns:
            Created resource or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/Observation",
                    json=observation_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Created Observation: {observation_data.get('id')}")
                    return response.json()
                else:
                    logger.error(f"Failed to create Observation: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error creating Observation in FHIR: {e}")
            return None
    
    async def create_condition(self, condition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a Condition resource in FHIR server
        
        Args:
            condition_data: FHIR Condition resource dict
            
        Returns:
            Created resource or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/Condition",
                    json=condition_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Created Condition: {condition_data.get('id')}")
                    return response.json()
                else:
                    logger.error(f"Failed to create Condition: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error creating Condition in FHIR: {e}")
            return None
    
    async def create_medication_request(self, med_request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a MedicationRequest resource in FHIR server
        
        Args:
            med_request_data: FHIR MedicationRequest resource dict
            
        Returns:
            Created resource or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/MedicationRequest",
                    json=med_request_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 201]:
                    logger.info(f"Created MedicationRequest: {med_request_data.get('id')}")
                    return response.json()
                else:
                    logger.error(f"Failed to create MedicationRequest: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error creating MedicationRequest in FHIR: {e}")
            return None
    
    async def check_connection(self) -> bool:
        """
        Check if FHIR server is reachable
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/metadata")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"FHIR server connection check failed: {e}")
            return False
# Create global FHIR service instance
fhir_service = FHIRService()
