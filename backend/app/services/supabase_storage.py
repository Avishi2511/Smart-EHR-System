"""
Supabase Storage Service for file uploads
Replaces local file storage with cloud storage
"""
from supabase import create_client, Client
import os
from typing import BinaryIO, Optional
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class SupabaseStorageService:
    """Service for managing file storage in Supabase"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured, file storage will not work")
            self.supabase = None
            self.bucket = None
        else:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.bucket = os.getenv("SUPABASE_BUCKET", "medical-files")
            logger.info(f"Supabase storage initialized with bucket: {self.bucket}")
    
    async def upload_file(self, file_path: str, file_data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        """
        Upload file to Supabase storage
        
        Args:
            file_path: Path within bucket (e.g., "patient-001/lab_reports/test.pdf")
            file_data: File binary data
            content_type: MIME type of file
            
        Returns:
            Public URL of uploaded file
        """
        if not self.supabase:
            raise Exception("Supabase not configured")
        
        try:
            # Read file data
            file_bytes = file_data.read()
            
            # Upload to Supabase
            result = self.supabase.storage.from_(self.bucket).upload(
                file_path,
                file_bytes,
                {"content-type": content_type}
            )
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket).get_public_url(file_path)
            
            logger.info(f"File uploaded successfully: {file_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from Supabase storage
        
        Args:
            file_path: Path within bucket
            
        Returns:
            File binary data
        """
        if not self.supabase:
            raise Exception("Supabase not configured")
        
        try:
            result = self.supabase.storage.from_(self.bucket).download(file_path)
            logger.info(f"File downloaded successfully: {file_path}")
            return result
        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from Supabase storage
        
        Args:
            file_path: Path within bucket
            
        Returns:
            True if successful
        """
        if not self.supabase:
            raise Exception("Supabase not configured")
        
        try:
            self.supabase.storage.from_(self.bucket).remove([file_path])
            logger.info(f"File deleted successfully: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise
    
    async def list_files(self, folder_path: str = "") -> list:
        """
        List files in a folder
        
        Args:
            folder_path: Folder path within bucket
            
        Returns:
            List of file metadata
        """
        if not self.supabase:
            raise Exception("Supabase not configured")
        
        try:
            result = self.supabase.storage.from_(self.bucket).list(folder_path)
            return result
        except Exception as e:
            logger.error(f"Failed to list files in {folder_path}: {e}")
            raise


# Global instance
supabase_storage = SupabaseStorageService()
