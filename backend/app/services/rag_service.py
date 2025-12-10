from typing import List, Dict, Any, Optional, Tuple
from app.services.vector_db import vector_db
from app.config import settings
import re
import logging
logger = logging.getLogger(__name__)
class RAGService:
    """Retrieval-Augmented Generation service for extracting information from documents"""
    
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD
    
    async def search_documents(
        self,
        query: str,
        patient_id: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks
        
        Args:
            query: Search query
            patient_id: Patient ID
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata and scores
        """
        k = top_k or self.top_k
        
        # Search vector database
        results = vector_db.search(query=query, patient_id=patient_id, top_k=k)
        
        # Format results
        formatted_results = []
        for metadata, score in results:
            if score >= self.similarity_threshold:
                formatted_results.append({
                    "text": metadata.get("text", ""),
                    "file_id": metadata.get("file_id"),
                    "chunk_index": metadata.get("chunk_index"),
                    "similarity_score": score,
                    "metadata": metadata
                })
        
        logger.info(f"Found {len(formatted_results)} relevant chunks for query: {query[:50]}...")
        return formatted_results
    
    async def extract_parameter_value(
        self,
        parameter_name: str,
        patient_id: str,
        context_query: Optional[str] = None
    ) -> Optional[Tuple[float, str, float]]:
        """
        Extract a specific parameter value from patient documents
        
        Args:
            parameter_name: Name of parameter to extract (e.g., "MMSE", "blood pressure")
            patient_id: Patient ID
            context_query: Optional additional context for search
            
        Returns:
            Tuple of (value, source_text, confidence) or None if not found
        """
        # Build search query
        query = f"{parameter_name}"
        if context_query:
            query = f"{parameter_name} {context_query}"
        
        # Search for relevant chunks
        results = await self.search_documents(query, patient_id, top_k=10)
        
        if not results:
            logger.info(f"No documents found for parameter: {parameter_name}")
            return None
        
        # Try to extract numeric value from results
        for result in results:
            text = result["text"]
            value = self._extract_numeric_value(text, parameter_name)
            
            if value is not None:
                confidence = result["similarity_score"]
                logger.info(f"Extracted {parameter_name}={value} with confidence {confidence}")
                return (value, text, confidence)
        
        logger.info(f"Could not extract numeric value for parameter: {parameter_name}")
        return None
    
    def _extract_numeric_value(self, text: str, parameter_name: str) -> Optional[float]:
        """
        Extract numeric value from text for a given parameter
        
        Args:
            text: Text to search
            parameter_name: Parameter name
            
        Returns:
            Extracted numeric value or None
        """
        # Normalize text
        text_lower = text.lower()
        param_lower = parameter_name.lower()
        
        # Common patterns for parameter extraction
        patterns = [
            # "Parameter: 120" or "Parameter = 120"
            rf"{re.escape(param_lower)}\s*[:=]\s*(\d+\.?\d*)",
            # "Parameter 120" or "Parameter is 120"
            rf"{re.escape(param_lower)}\s+(?:is\s+)?(\d+\.?\d*)",
            # "120 Parameter" (value before parameter)
            rf"(\d+\.?\d*)\s+{re.escape(param_lower)}",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    value = float(match.group(1))
                    return value
                except ValueError:
                    continue
        
        # Try to find any number in the text as fallback
        numbers = re.findall(r'\d+\.?\d*', text)
        if numbers:
            try:
                # Return the first number found
                return float(numbers[0])
            except ValueError:
                pass
        
        return None
    
    async def extract_multiple_parameters(
        self,
        parameter_names: List[str],
        patient_id: str
    ) -> Dict[str, Optional[Tuple[float, str, float]]]:
        """
        Extract multiple parameter values from patient documents
        
        Args:
            parameter_names: List of parameter names to extract
            patient_id: Patient ID
            
        Returns:
            Dictionary mapping parameter names to (value, source, confidence) tuples
        """
        results = {}
        
        for param_name in parameter_names:
            result = await self.extract_parameter_value(param_name, patient_id)
            results[param_name] = result
        
        return results
    
    async def answer_query(
        self,
        query: str,
        patient_id: str
    ) -> Dict[str, Any]:
        """
        Answer a natural language query using RAG
        
        Args:
            query: Natural language query
            patient_id: Patient ID
            
        Returns:
            Dictionary with answer and sources
        """
        # Search for relevant documents
        results = await self.search_documents(query, patient_id, top_k=5)
        
        if not results:
            return {
                "query": query,
                "answer": "No relevant information found in patient documents.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Combine top results as context
        context_chunks = [r["text"] for r in results[:3]]
        context = "\n\n".join(context_chunks)
        
        # For now, return the most relevant chunk as the answer
        # In production, you could use an LLM to generate a better answer
        answer = results[0]["text"]
        confidence = results[0]["similarity_score"]
        
        sources = [
            {
                "file_id": r["file_id"],
                "chunk_index": r["chunk_index"],
                "similarity_score": r["similarity_score"],
                "text_preview": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"]
            }
            for r in results
        ]
        
        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }
    
    async def find_missing_parameters(
        self,
        required_parameters: List[str],
        available_parameters: Dict[str, float],
        patient_id: str
    ) -> Dict[str, Optional[Tuple[float, str, float]]]:
        """
        Find missing parameters using RAG
        
        Args:
            required_parameters: List of all required parameter names
            available_parameters: Dictionary of already available parameters
            patient_id: Patient ID
            
        Returns:
            Dictionary of extracted missing parameters
        """
        missing_params = [p for p in required_parameters if p not in available_parameters]
        
        if not missing_params:
            logger.info("No missing parameters to extract")
            return {}
        
        logger.info(f"Attempting to extract {len(missing_params)} missing parameters: {missing_params}")
        
        extracted = await self.extract_multiple_parameters(missing_params, patient_id)
        
        # Filter out None values
        found_params = {k: v for k, v in extracted.items() if v is not None}
        
        logger.info(f"Successfully extracted {len(found_params)} missing parameters")
        return found_params
    
    def get_context_for_parameter(self, parameter_name: str) -> str:
        """
        Get additional context/synonyms for a parameter to improve search
        
        Args:
            parameter_name: Parameter name
            
        Returns:
            Additional search context
        """
        # Common parameter synonyms and contexts
        context_map = {
            "mmse": "mini mental state examination cognitive score",
            "bp": "blood pressure systolic diastolic",
            "systolic_bp": "systolic blood pressure",
            "diastolic_bp": "diastolic blood pressure",
            "heart_rate": "pulse heart rate bpm",
            "glucose": "blood glucose sugar level",
            "hba1c": "hemoglobin a1c glycated",
            "cholesterol": "total cholesterol lipid",
            "bmi": "body mass index weight height",
            "temperature": "body temperature fever",
            "weight": "body weight kg pounds",
            "height": "body height cm inches",
        }
        
        param_lower = parameter_name.lower()
        return context_map.get(param_lower, "")
# Create global RAG service instance
rag_service = RAGService()
