from pydantic_settings import BaseSettings
from typing import List
import os
class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./backend.db"
    
    # FHIR Server Configuration
    FHIR_SERVER_URL: str = "http://localhost:8000"
    FHIR_SERVER_TIMEOUT: int = 30
    
    # File Storage Configuration
    FILE_STORAGE_PATH: str = "./storage/files"
    MAX_FILE_SIZE_MB: int = 50
    
    # Supabase Storage Configuration (for cloud deployment)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_BUCKET: str = "files"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OpenAI Configuration (optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # CORS Configuration
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
# Create global settings instance
settings = Settings()
# Ensure storage directories exist
os.makedirs(settings.FILE_STORAGE_PATH, exist_ok=True)
