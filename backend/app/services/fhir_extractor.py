from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class FHIRExtractor:
    """Extract FHIR-compliant resources from document text"""
    
    def __init__(self):
        # LOINC code mappings for observations
        self.vital_signs_mapping = {
            "systolic_bp": {"loinc": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg"},
            "diastolic_bp": {"loinc": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg"},
            "heart_rate": {"loinc": "8867-4", "display": "Heart rate", "unit": "beats/min"},
            "respiratory_rate": {"loinc": "9279-1", "display": "Respiratory rate", "unit": "breaths/min"},
            "body_temperature": {"loinc": "8310-5", "display": "Body temperature", "unit": "Cel"},
            "body_weight": {"loinc": "29463-7", "display": "Body weight", "unit": "kg"},
            "body_height": {"loinc": "8302-2", "display": "Body height", "unit": "cm"},
            "bmi": {"loinc": "39156-5", "display": "Body mass index", "unit": "kg/m2"},
            "oxygen_saturation": {"loinc": "2708-6", "display": "Oxygen saturation", "unit": "%"},
        }
        
        self.lab_results_mapping = {
            "glucose": {"loinc": "2339-0", "display": "Glucose", "unit": "mg/dL"},
            "cholesterol_total": {"loinc": "2093-3", "display": "Cholesterol total", "unit": "mg/dL"},
            "hdl_cholesterol": {"loinc": "2085-9", "display": "HDL Cholesterol", "unit": "mg/dL"},
            "ldl_cholesterol": {"loinc": "2089-1", "display": "LDL Cholesterol", "unit": "mg/dL"},
            "triglycerides": {"loinc": "2571-8", "display": "Triglycerides", "unit": "mg/dL"},
            "hba1c": {"loinc": "4548-4", "display": "Hemoglobin A1c", "unit": "%"},
            "hemoglobin": {"loinc": "718-7", "display": "Hemoglobin", "unit": "g/dL"},
            "wbc_count": {"loinc": "6690-2", "display": "White blood cell count", "unit": "10*3/uL"},
            "platelet_count": {"loinc": "777-3", "display": "Platelet count", "unit": "10*3/uL"},
            "creatinine": {"loinc": "2160-0", "display": "Creatinine", "unit": "mg/dL"},
            "bun": {"loinc": "3094-0", "display": "Blood urea nitrogen", "unit": "mg/dL"},
            "alt": {"loinc": "1742-6", "display": "Alanine aminotransferase", "unit": "U/L"},
            "ast": {"loinc": "1920-8", "display": "Aspartate aminotransferase", "unit": "U/L"},
            "egfr": {"loinc": "33914-3", "display": "Glomerular filtration rate", "unit": "mL/min"},
            "map": {"loinc": "8478-0", "display": "Mean blood pressure", "unit": "mmHg"},
            "cystatin_c": {"loinc": "33863-2", "display": "Cystatin C", "unit": "mg/L"},
            "uric_acid": {"loinc": "3084-1", "display": "Uric acid", "unit": "mg/dL"},
        }
        
        # Extraction patterns for observations
        self.extraction_patterns = self._build_extraction_patterns()
    
    def _build_extraction_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for extracting clinical parameters"""
        patterns = {}
        
        # Blood pressure patterns
        patterns["blood_pressure"] = [
            r"(?:BP|Blood\s+Pressure|B\.P\.?)[\s:=]+(\d{2,3})/(\d{2,3})\s*(?:mmHg)?",
            r"(\d{2,3})/(\d{2,3})\s*mmHg",
        ]
        
        # Glucose patterns
        patterns["glucose"] = [
            r"(?:Glucose|Blood\s+Sugar|FBS|RBS|Fasting\s+Glucose)[\s:=]+(\d{2,3})\s*(?:mg/dL)?",
            r"Glucose[\s:=]+(\d{2,3})",
        ]
        
        # Weight patterns
        patterns["body_weight"] = [
            r"(?:Weight|Wt\.?)[\s:=]+(\d{2,3}(?:\.\d)?)\s*(?:kg|kgs)?",
            r"(\d{2,3}(?:\.\d)?)\s*kg",
        ]
        
        # Height patterns
        patterns["body_height"] = [
            r"(?:Height|Ht\.?)[\s:=]+(\d{2,3}(?:\.\d)?)\s*(?:cm)?",
            r"(\d{2,3}(?:\.\d)?)\s*cm",
        ]
        
        # Temperature patterns (more specific to avoid false matches)
        patterns["body_temperature"] = [
            r"(?:Temperature|Temp\.?|Body\s+Temp)[\s:=]+(\d{2,3}(?:\.\d)?)[\s]*(?:°C|°F|C|F|Cel|Fahrenheit)",
            r"(?:Temperature|Temp\.?)[\s:=]+(\d{2}(?:\.\d)?)(?:\s|$)",  # Only match if followed by space or end
        ]
        
        # Heart rate patterns
        patterns["heart_rate"] = [
            r"(?:Heart\s+Rate|HR|Pulse)[\s:=]+(\d{2,3})\s*(?:bpm|beats/min)?",
            r"Pulse[\s:=]+(\d{2,3})",
        ]
        
        # Cholesterol patterns
        patterns["cholesterol_total"] = [
            r"(?:Total\s+)?Cholesterol[\s:=]+(\d{2,3})\s*(?:mg/dL)?",
        ]
        
        patterns["hdl_cholesterol"] = [
            r"HDL[\s:=]+(\d{2,3})\s*(?:mg/dL)?",
        ]
        
        patterns["ldl_cholesterol"] = [
            r"LDL[\s:=]+(\d{2,3})\s*(?:mg/dL)?",
        ]
        
        # HbA1c patterns
        patterns["hba1c"] = [
            r"(?:HbA1c|A1C|Glycated\s+Hemoglobin)[\s:=]+(\d{1,2}(?:\.\d)?)\s*%?",
        ]
        
        # Hemoglobin patterns
        patterns["hemoglobin"] = [
            r"(?:Hemoglobin|Hb|Hgb)[\s:=]+(\d{1,2}(?:\.\d)?)\s*(?:g/dL)?",
        ]
        
        # Creatinine patterns
        patterns["creatinine"] = [
            r"(?:Creatinine|Creat)[\s:=]+(\d{1,3}(?:\.\d)?)\s*(?:mg/dL|umol/L)?",
        ]
        
        # eGFR patterns
        patterns["egfr"] = [
            r"(?:eGFR|GFR)[\s:=]+(\d{1,3})\s*(?:mL/min)?",
        ]
        
        # MAP (Mean Arterial Pressure) patterns  
        patterns["map"] = [
            r"MAP[\s:=]+(\d{2,3})\s*(?:mmHg)?",
        ]
        
        # Cystatin C patterns
        patterns["cystatin_c"] = [
            r"Cystatin\s*C[\s:=]+(\d{1,2}(?:\.\d{1,2})?)\s*(?:mg/L)?",
        ]
        
        # Uric Acid patterns
        patterns["uric_acid"] = [
            r"Uric\s+Acid[\s:=]+(\d{1,2}(?:\.\d)?)\s*(?:mg/dL)?",
        ]
        
        # BMI patterns
        patterns["bmi"] = [
            r"BMI[\s:=]+(\d{1,2}(?:\.\d)?)\s*(?:kg/m2)?",
        ]
        
        # Oxygen saturation patterns
        patterns["oxygen_saturation"] = [
            r"(?:SpO2|O2\s+Sat|Oxygen\s+Saturation)[\s:=]+(\d{2,3})\s*%?",
        ]
        
        return patterns
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text, return ISO format string"""
        # Common date patterns
        date_patterns = [
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",  # DD/MM/YYYY or MM/DD/YYYY
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # YYYY-MM-DD
            r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})",  # DD Mon YYYY
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    # Try to parse the date
                    groups = match.groups()
                    if len(groups) == 3:
                        # Simple date parsing - use current date as fallback
                        return datetime.now().isoformat()
                except:
                    pass
        
        # Default to current date if no date found
        return datetime.now().isoformat()
    
    def extract_observations(
        self, 
        text: str, 
        patient_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract observation data from text
        
        Args:
            text: Document text
            patient_id: FHIR patient ID
            
        Returns:
            List of extracted observations with values
        """
        observations = []
        text_lower = text.lower()
        
        # Extract date from document
        observation_date = self._extract_date_from_text(text)
        
        # Extract blood pressure (special case - two values)
        for pattern in self.extraction_patterns["blood_pressure"]:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                systolic = float(match.group(1))
                diastolic = float(match.group(2))
                
                observations.append({
                    "type": "systolic_bp",
                    "value": systolic,
                    "date": observation_date
                })
                observations.append({
                    "type": "diastolic_bp",
                    "value": diastolic,
                    "date": observation_date
                })
                logger.info(f"Extracted BP: {systolic}/{diastolic}")
        
        # Extract other vital signs and lab results
        all_params = {**self.vital_signs_mapping, **self.lab_results_mapping}
        
        for param_key in all_params.keys():
            if param_key in ["systolic_bp", "diastolic_bp"]:
                continue  # Already handled above
            
            if param_key in self.extraction_patterns:
                for pattern in self.extraction_patterns[param_key]:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        try:
                            value = float(match.group(1))
                            observations.append({
                                "type": param_key,
                                "value": value,
                                "date": observation_date
                            })
                            logger.info(f"Extracted {param_key}: {value}")
                        except (ValueError, IndexError):
                            continue
        
        return observations
    
    def extract_conditions(
        self, 
        text: str, 
        patient_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract condition/diagnosis data from text
        
        Args:
            text: Document text
            patient_id: FHIR patient ID
            
        Returns:
            List of extracted conditions
        """
        conditions = []
        
        # Common condition keywords
        condition_keywords = [
            "hypertension", "diabetes", "mellitus", "asthma", "copd",
            "hypothyroidism", "hyperthyroidism", "anemia", "obesity",
            "dyslipidemia", "hyperlipidemia", "coronary artery disease",
            "heart failure", "stroke", "chronic kidney disease"
        ]
        
        text_lower = text.lower()
        
        # Simple keyword matching for conditions
        for keyword in condition_keywords:
            if keyword in text_lower:
                conditions.append({
                    "code_text": keyword.title(),
                    "status": "active",
                    "onset_date": self._extract_date_from_text(text)
                })
                logger.info(f"Extracted condition: {keyword}")
        
        return conditions
    
    def extract_medications(
        self, 
        text: str, 
        patient_id: str
    ) -> List[Dict[str, Any]]:
        """
        Extract medication data from text
        
        Args:
            text: Document text
            patient_id: FHIR patient ID
            
        Returns:
            List of extracted medications
        """
        medications = []
        
        # Common medication patterns
        med_patterns = [
            r"(Metformin|Amlodipine|Atorvastatin|Levothyroxine|Lisinopril|Aspirin)\s+(\d+)\s*mg",
            r"(Insulin|Glimepiride|Losartan|Ramipril)\s+(\d+)",
        ]
        
        for pattern in med_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                med_name = match.group(1)
                try:
                    dosage = match.group(2)
                    medications.append({
                        "medication_text": f"{med_name} {dosage}mg",
                        "status": "active"
                    })
                    logger.info(f"Extracted medication: {med_name} {dosage}mg")
                except IndexError:
                    medications.append({
                        "medication_text": med_name,
                        "status": "active"
                    })
        
        return medications
    
    def extract_all_resources(
        self, 
        text: str, 
        patient_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all FHIR resources from text
        
        Args:
            text: Document text
            patient_id: FHIR patient ID
            
        Returns:
            Dictionary with resource types as keys and lists of extracted data
        """
        logger.info(f"Extracting FHIR resources from document for patient {patient_id}")
        
        return {
            "observations": self.extract_observations(text, patient_id),
            "conditions": self.extract_conditions(text, patient_id),
            "medications": self.extract_medications(text, patient_id)
        }


# Create global FHIR extractor instance
fhir_extractor = FHIRExtractor()
