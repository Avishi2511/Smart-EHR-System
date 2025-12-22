from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
import logging
from app.services.fhir_service import fhir_service

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process natural language queries and retrieve FHIR data"""
    
    def __init__(self):
        # Parameter name mappings (query terms -> FHIR codes)
        self.parameter_mappings = {
            "blood pressure": ["8480-6", "8462-4"],  # Systolic and Diastolic
            "bp": ["8480-6", "8462-4"],
            "systolic": ["8480-6"],
            "diastolic": ["8462-4"],
            "glucose": ["2339-0"],
            "blood sugar": ["2339-0"],
            "heart rate": ["8867-4"],
            "pulse": ["8867-4"],
            "temperature": ["8310-5"],
            "weight": ["29463-7"],
            "height": ["8302-2"],
            "bmi": ["39156-5"],
            "cholesterol": ["2093-3"],
            "hdl": ["2085-9"],
            "ldl": ["2089-1"],
            "hba1c": ["4548-4"],
            "a1c": ["4548-4"],
            "hemoglobin": ["718-7"],
            "creatinine": ["2160-0"],
            "egfr": ["33914-3"],
            "oxygen": ["2708-6"],
            "spo2": ["2708-6"],
        }
        
        # Query type patterns
        self.query_patterns = {
            "latest": r"(?:latest|most recent|current|last reading)",
            "time_series": r"(?:last|past|previous)\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)",
            "all": r"(?:all|every|complete history)",
            "average": r"(?:average|mean|avg)",
            "trend": r"(?:trend|pattern|over time)",
            "range": r"(?:between|from)\s+(.+?)\s+(?:to|and)\s+(.+)",
        }
    
    def parse_query(self, query: str, patient_id: str) -> Dict[str, Any]:
        """
        Parse natural language query and extract intent
        
        Args:
            query: Natural language query
            patient_id: FHIR patient ID
            
        Returns:
            Parsed query information
        """
        query_lower = query.lower()
        
        # Determine query type
        query_type = self._determine_query_type(query_lower)
        
        # Extract parameters
        parameters = self._extract_parameters(query_lower)
        
        # Extract time period
        time_period = self._extract_time_period(query_lower)
        
        # Extract aggregation type
        aggregation = self._extract_aggregation(query_lower)
        
        return {
            "original_query": query,
            "query_type": query_type,
            "parameters": parameters,
            "time_period": time_period,
            "aggregation": aggregation,
            "patient_id": patient_id
        }
    
    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query"""
        if re.search(self.query_patterns["latest"], query):
            return "latest"
        elif re.search(self.query_patterns["time_series"], query):
            return "time_series"
        elif re.search(self.query_patterns["all"], query):
            return "all"
        elif re.search(self.query_patterns["average"], query):
            return "average"
        elif re.search(self.query_patterns["trend"], query):
            return "trend"
        else:
            return "general"
    
    def _extract_parameters(self, query: str) -> List[str]:
        """Extract clinical parameters from query"""
        found_params = []
        
        for param_name, loinc_codes in self.parameter_mappings.items():
            if param_name in query:
                found_params.extend(loinc_codes)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(found_params))
    
    def _extract_time_period(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract time period from query"""
        # Pattern: "last N days/weeks/months/years"
        match = re.search(self.query_patterns["time_series"], query)
        if match:
            amount = int(match.group(1))
            unit = match.group(2).rstrip('s')  # Remove plural 's'
            
            # Calculate start date
            now = datetime.now()
            if unit == "day":
                start_date = now - timedelta(days=amount)
            elif unit == "week":
                start_date = now - timedelta(weeks=amount)
            elif unit == "month":
                start_date = now - timedelta(days=amount * 30)  # Approximate
            elif unit == "year":
                start_date = now - timedelta(days=amount * 365)  # Approximate
            else:
                return None
            
            return {
                "amount": amount,
                "unit": unit,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat()
            }
        
        return None
    
    def _extract_aggregation(self, query: str) -> Optional[str]:
        """Extract aggregation type from query"""
        if "average" in query or "mean" in query:
            return "average"
        elif "minimum" in query or "min" in query or "lowest" in query:
            return "min"
        elif "maximum" in query or "max" in query or "highest" in query:
            return "max"
        elif "trend" in query or "pattern" in query:
            return "trend"
        return None
    
    async def execute_query(self, parsed_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the parsed query against FHIR server
        
        Args:
            parsed_query: Parsed query information
            
        Returns:
            Query results with data and metadata
        """
        patient_id = parsed_query["patient_id"]
        query_type = parsed_query["query_type"]
        parameters = parsed_query["parameters"]
        time_period = parsed_query["time_period"]
        
        try:
            # Check if query is about medications (doesn't need parameters)
            if "medication" in parsed_query["original_query"].lower():
                return await self._query_medications(patient_id)
            
            # Check if query is about conditions (doesn't need parameters)
            if "condition" in parsed_query["original_query"].lower() or "diagnosis" in parsed_query["original_query"].lower() or "diagnoses" in parsed_query["original_query"].lower():
                return await self._query_conditions(patient_id)
            
            # For observations, we need parameters
            if not parameters:
                return {
                    "success": False,
                    "error": "I couldn't find any specific health parameters in your query. Try asking about blood pressure, glucose, medications, or diagnoses.",
                    "query": parsed_query["original_query"]
                }
            
            # Query observations
            if query_type == "latest":
                return await self._query_latest_observations(patient_id, parameters)
            elif query_type in ["time_series", "all", "trend"]:
                return await self._query_time_series_observations(
                    patient_id, 
                    parameters, 
                    time_period
                )
            elif query_type == "average":
                return await self._query_average_observations(
                    patient_id, 
                    parameters, 
                    time_period
                )
            else:
                # Default to time series
                return await self._query_time_series_observations(
                    patient_id, 
                    parameters, 
                    time_period
                )
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return {
                "success": False,
                "error": "I encountered an issue processing your query. Please try rephrasing or ask about medications, diagnoses, or specific health measurements.",
                "query": parsed_query["original_query"]
            }
    
    async def _query_latest_observations(
        self, 
        patient_id: str, 
        loinc_codes: List[str]
    ) -> Dict[str, Any]:
        """Query for latest observations"""
        results = []
        
        for code in loinc_codes:
            observations = await fhir_service.get_observations_by_code(
                patient_id=patient_id,
                loinc_code=code
            )
            
            if observations:
                # Sort by date and get the latest
                sorted_obs = sorted(
                    observations,
                    key=lambda x: x.get("effectiveDateTime", ""),
                    reverse=True
                )
                if sorted_obs:
                    latest = sorted_obs[0]
                    results.append({
                        "code": code,
                        "display": latest.get("code", {}).get("coding", [{}])[0].get("display", "Unknown"),
                        "value": latest.get("valueQuantity", {}).get("value"),
                        "unit": latest.get("valueQuantity", {}).get("unit"),
                        "date": latest.get("effectiveDateTime"),
                        "id": latest.get("id")
                    })
        
        return {
            "success": True,
            "query_type": "latest",
            "data": results,
            "count": len(results)
        }
    
    async def _query_time_series_observations(
        self, 
        patient_id: str, 
        loinc_codes: List[str],
        time_period: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Query for time series observations"""
        results = []
        
        for code in loinc_codes:
            observations = await fhir_service.get_observations_by_code(
                patient_id=patient_id,
                loinc_code=code
            )
            
            if observations:
                # Filter by time period if specified
                filtered_obs = observations
                if time_period:
                    start_date = time_period["start_date"]
                    filtered_obs = [
                        obs for obs in observations
                        if obs.get("effectiveDateTime", "") >= start_date
                    ]
                
                # Sort by date
                sorted_obs = sorted(
                    filtered_obs,
                    key=lambda x: x.get("effectiveDateTime", "")
                )
                
                # Format results
                for obs in sorted_obs:
                    results.append({
                        "code": code,
                        "display": obs.get("code", {}).get("coding", [{}])[0].get("display", "Unknown"),
                        "value": obs.get("valueQuantity", {}).get("value"),
                        "unit": obs.get("valueQuantity", {}).get("unit"),
                        "date": obs.get("effectiveDateTime"),
                        "id": obs.get("id")
                    })
        
        return {
            "success": True,
            "query_type": "time_series",
            "data": results,
            "count": len(results),
            "time_period": time_period
        }
    
    async def _query_average_observations(
        self, 
        patient_id: str, 
        loinc_codes: List[str],
        time_period: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Query for average observations"""
        # First get time series data
        time_series = await self._query_time_series_observations(
            patient_id, 
            loinc_codes, 
            time_period
        )
        
        if not time_series["success"]:
            return time_series
        
        # Calculate averages by code
        averages = {}
        for item in time_series["data"]:
            code = item["code"]
            if code not in averages:
                averages[code] = {
                    "display": item["display"],
                    "unit": item["unit"],
                    "values": []
                }
            if item["value"] is not None:
                averages[code]["values"].append(item["value"])
        
        # Compute averages
        results = []
        for code, data in averages.items():
            if data["values"]:
                avg_value = sum(data["values"]) / len(data["values"])
                results.append({
                    "code": code,
                    "display": data["display"],
                    "average": round(avg_value, 2),
                    "unit": data["unit"],
                    "count": len(data["values"])
                })
        
        return {
            "success": True,
            "query_type": "average",
            "data": results,
            "time_period": time_period
        }
    
    async def _query_medications(self, patient_id: str) -> Dict[str, Any]:
        """Query for medications"""
        medications = await fhir_service.get_medication_requests(patient_id)
        
        results = []
        for med in medications:
            results.append({
                "medication": med.get("medicationCodeableConcept", {}).get("text", "Unknown"),
                "status": med.get("status", "unknown"),
                "date": med.get("authoredOn"),
                "id": med.get("id")
            })
        
        return {
            "success": True,
            "query_type": "medications",
            "data": results,
            "count": len(results)
        }
    
    async def _query_conditions(self, patient_id: str) -> Dict[str, Any]:
        """Query for conditions"""
        conditions = await fhir_service.get_conditions(patient_id)
        
        results = []
        for cond in conditions:
            results.append({
                "condition": cond.get("code", {}).get("text", "Unknown"),
                "status": cond.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "unknown"),
                "onset": cond.get("onsetDateTime"),
                "id": cond.get("id")
            })
        
        return {
            "success": True,
            "query_type": "conditions",
            "data": results,
            "count": len(results)
        }
    
    def get_suggested_queries(self, patient_id: str) -> List[str]:
        """Get suggested queries based on common patterns"""
        return [
            "What was the patient's blood pressure in the last 3 months?",
            "Show me the latest glucose readings",
            "What medications is the patient taking?",
            "What are the patient's current diagnoses?",
            "Show all lab results from the last 6 months",
            "What is the average heart rate over the past month?",
            "Show the patient's weight trend over the last year"
        ]


# Create global query processor instance
query_processor = QueryProcessor()
