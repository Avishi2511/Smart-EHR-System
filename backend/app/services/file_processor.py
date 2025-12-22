import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import PyPDF2
from PIL import Image
import pytesseract
from docx import Document
from app.config import settings
from app.models.sql_models import File
from app.services.fhir_extractor import fhir_extractor
from app.services.fhir_resource_builder import fhir_resource_builder
from app.services.fhir_service import fhir_service
from sqlalchemy.orm import Session
import logging
logger = logging.getLogger(__name__)
class FileProcessor:
    """Service for processing uploaded files and extracting text"""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"Extracted {len(text)} characters from PDF: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    def extract_text_from_image(self, file_path: str) -> str:
        """
        Extract text from image using OCR
        
        Args:
            file_path: Path to image file
            
        Returns:
            Extracted text
        """
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            logger.info(f"Extracted {len(text)} characters from image: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {e}")
            raise
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            logger.info(f"Extracted {len(text)} characters from DOCX: {file_path}")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """
        Extract text from file based on type
        
        Args:
            file_path: Path to file
            file_type: Type of file (pdf, image, document, note)
            
        Returns:
            Extracted text
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_type == "pdf" or file_extension == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif file_type == "image" or file_extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return self.extract_text_from_image(file_path)
        elif file_type == "document" or file_extension == ".docx":
            return self.extract_text_from_docx(file_path)
        elif file_type == "note" or file_extension == ".txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return ""
    
    async def process_file(
        self,
        db: Session,
        file_id: str,
        patient_id: str,
        fhir_patient_id: str,
        file_path: str,
        file_type: str
    ) -> bool:
        """
        Process a file: extract text, extract FHIR resources, and store in FHIR server
        
        Args:
            db: Database session
            file_id: File ID
            patient_id: Patient ID (backend)
            fhir_patient_id: FHIR patient ID
            file_path: Path to file
            file_type: Type of file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract text from file
            logger.info(f"Processing file {file_id}: {file_path}")
            text = self.extract_text_from_file(file_path, file_type)
            
            if not text:
                logger.warning(f"No text extracted from file {file_id}")
                return False
            
            # Extract FHIR resources from text
            extracted_data = fhir_extractor.extract_all_resources(text, fhir_patient_id)
            
            resource_count = 0
            
            # Create Observation resources
            for obs_data in extracted_data.get("observations", []):
                observation = fhir_resource_builder.build_observation(
                    observation_type=obs_data["type"],
                    value=obs_data["value"],
                    patient_id=fhir_patient_id,
                    effective_date=obs_data.get("date")
                )
                
                result = await fhir_service.create_observation(observation)
                if result:
                    resource_count += 1
            
            # Create Condition resources
            for cond_data in extracted_data.get("conditions", []):
                condition = fhir_resource_builder.build_condition(
                    code_text=cond_data["code_text"],
                    patient_id=fhir_patient_id,
                    clinical_status=cond_data.get("status", "active"),
                    onset_date=cond_data.get("onset_date")
                )
                
                result = await fhir_service.create_condition(condition)
                if result:
                    resource_count += 1
            
            # Create MedicationRequest resources
            for med_data in extracted_data.get("medications", []):
                medication_request = fhir_resource_builder.build_medication_request(
                    medication_text=med_data["medication_text"],
                    patient_id=fhir_patient_id,
                    status=med_data.get("status", "active")
                )
                
                result = await fhir_service.create_medication_request(medication_request)
                if result:
                    resource_count += 1
            
            # Update file as processed
            file_record = db.query(File).filter(File.id == file_id).first()
            if file_record:
                file_record.processed = True
                file_record.processed_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Successfully processed file {file_id} - created {resource_count} FHIR resources")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            db.rollback()
            
            # Update file with error
            file_record = db.query(File).filter(File.id == file_id).first()
            if file_record:
                file_record.processing_error = str(e)
                db.commit()
            
            return False
    
    async def process_unprocessed_files(self, db: Session) -> int:
        """
        Process all unprocessed files in the database
        
        Args:
            db: Database session
            
        Returns:
            Number of files processed
        """
        unprocessed_files = db.query(File).filter(File.processed == False).all()
        
        logger.info(f"Found {len(unprocessed_files)} unprocessed files")
        
        processed_count = 0
        for file_record in unprocessed_files:
            success = await self.process_file(
                db=db,
                file_id=file_record.id,
                patient_id=file_record.patient_id,
                file_path=file_record.file_path,
                file_type=file_record.file_type.value
            )
            
            if success:
                processed_count += 1
        
        logger.info(f"Processed {processed_count} files")
        return processed_count
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file metadata
        """
        try:
            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "extension": os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            return {}
# Create global file processor instance
file_processor = FileProcessor()
