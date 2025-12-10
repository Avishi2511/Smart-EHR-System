from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging
from app.config import settings
from app.database import init_db
from app.models.schemas import HealthCheckResponse
from app.api import patients, files, models, queries
from app.services.fhir_service import fhir_service
from app.services.vector_db import vector_db
# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Create FastAPI application
app = FastAPI(
    title="Smart EHR Backend",
    description="Backend system with SQL, Vector DB, and RAG for Smart EHR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("Starting Smart EHR Backend...")
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Check FHIR server connection
    fhir_connected = await fhir_service.check_connection()
    if fhir_connected:
        logger.info("✓ FHIR server connection successful")
    else:
        logger.warning("✗ FHIR server connection failed")
    
    # Check vector database
    vector_db_ready = vector_db.is_initialized()
    if vector_db_ready:
        logger.info("✓ Vector database initialized")
        stats = vector_db.get_stats()
        logger.info(f"  - Total vectors: {stats['total_vectors']}")
        logger.info(f"  - Patients: {stats['patients']}")
    else:
        logger.warning("✗ Vector database not initialized")
    
    logger.info("Smart EHR Backend started successfully!")
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Smart EHR Backend...")
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Smart EHR Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    # Check database connection
    try:
        from app.database import engine
        with engine.connect() as conn:
            database_connected = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_connected = False
    
    # Check FHIR server
    fhir_server_reachable = await fhir_service.check_connection()
    
    # Check vector database
    vector_db_initialized = vector_db.is_initialized()
    
    return HealthCheckResponse(
        status="healthy" if all([database_connected, vector_db_initialized]) else "degraded",
        service="Smart EHR Backend",
        timestamp=datetime.utcnow(),
        database_connected=database_connected,
        vector_db_initialized=vector_db_initialized,
        fhir_server_reachable=fhir_server_reachable
    )
# Include routers
app.include_router(patients.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
