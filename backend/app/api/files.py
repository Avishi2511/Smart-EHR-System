from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
from app.database import get_db
from app.models.sql_models import File, Patient, FileType, FileCategory
from app.models.schemas import FileResponse, FileUploadResponse
from app.services.file_processor import file_processor
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["Files"])


def get_file_type(filename: str) -> FileType:
    """Determine file type from filename"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        return FileType.PDF
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
        return FileType.IMAGE
    elif ext in [".doc", ".docx"]:
        return FileType.DOCUMENT
    elif ext == ".txt":
        return FileType.NOTE
    else:
        return FileType.OTHER


@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    patient_id: str = Form(...),
    category: str = Form(...),
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for a patient
    
    File is saved to storage and metadata is stored in database.
    File will be processed asynchronously to extract text and create embeddings.
    """
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Determine file type
    file_type = get_file_type(file.filename)
    
    # Validate category
    try:
        file_category = FileCategory(category)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {[c.value for c in FileCategory]}"
        )
    
    # Create patient directory if it doesn't exist
    patient_dir = os.path.join(settings.FILE_STORAGE_PATH, patient_id)
    os.makedirs(patient_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(patient_dir, safe_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error saving file"
        )
    
    # Create database record
    db_file = File(
        patient_id=patient_id,
        filename=file.filename,
        file_type=file_type,
        category=file_category,
        file_path=file_path,
        file_size=file_size,
        processed=False
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    logger.info(f"Uploaded file {db_file.id} for patient {patient_id}")
    
    # Process file asynchronously
    try:
        await file_processor.process_file(
            db=db,
            file_id=db_file.id,
            patient_id=patient_id,
            file_path=file_path,
            file_type=file_type.value
        )
    except Exception as e:
        logger.error(f"Error processing file {db_file.id}: {e}")
        # File is saved but processing failed - will be retried later
    
    return FileUploadResponse(
        file_id=db_file.id,
        filename=file.filename,
        message="File uploaded successfully and queued for processing"
    )


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get file metadata"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    
    return file


@router.get("/patient/{patient_id}", response_model=List[FileResponse])
async def list_patient_files(
    patient_id: str,
    category: Optional[str] = None,
    processed_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all files for a patient"""
    query = db.query(File).filter(File.patient_id == patient_id)
    
    if category:
        try:
            file_category = FileCategory(category)
            query = query.filter(File.category == file_category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {[c.value for c in FileCategory]}"
            )
    
    if processed_only:
        query = query.filter(File.processed == True)
    
    files = query.order_by(File.uploaded_at.desc()).all()
    return files


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Delete a file and its embeddings"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    
    # Delete from vector database
    from app.services.vector_db import vector_db
    vector_db.delete_by_file(file_id)
    
    # Delete physical file
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        logger.error(f"Error deleting physical file: {e}")
    
    # Delete from database
    db.delete(file)
    db.commit()
    
    logger.info(f"Deleted file {file_id}")


@router.post("/{file_id}/reprocess")
async def reprocess_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Reprocess a file to regenerate embeddings"""
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    
    # Delete existing embeddings
    from app.services.vector_db import vector_db
    vector_db.delete_by_file(file_id)
    
    # Reset processing status
    file.processed = False
    file.processing_error = None
    file.processed_at = None
    db.commit()
    
    # Reprocess
    success = await file_processor.process_file(
        db=db,
        file_id=file_id,
        patient_id=file.patient_id,
        file_path=file.file_path,
        file_type=file.file_type.value
    )
    
    if success:
        return {"message": "File reprocessed successfully", "file_id": file_id}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reprocessing file"
        )


@router.post("/process-unprocessed")
async def process_unprocessed_files(
    db: Session = Depends(get_db)
):
    """Process all unprocessed files"""
    count = await file_processor.process_unprocessed_files(db)
    
    return {
        "message": f"Processed {count} files",
        "files_processed": count
    }


@router.get("/stats/processing-status")
async def get_processing_status(
    db: Session = Depends(get_db)
):
    """Get file processing statistics"""
    total_files = db.query(File).count()
    processed_files = db.query(File).filter(File.processed == True).count()
    failed_files = db.query(File).filter(File.processing_error.isnot(None)).count()
    pending_files = total_files - processed_files
    
    return {
        "total_files": total_files,
        "processed_files": processed_files,
        "pending_files": pending_files,
        "failed_files": failed_files
    }
