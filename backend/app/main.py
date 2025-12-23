from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import logging
from app.config import settings
from app.database import init_db
from app.models.schemas import HealthCheckResponse
from app.api import patients, files, models, queries, chat, alzheimers, analytics, observations
from app.services.fhir_service import fhir_service
# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Create FastAPI application
app = FastAPI(
    title="Smart EHR Backend",
    description="Backend system with FHIR integration for Smart EHR",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://smart-ehr-system.vercel.app",
        "https://*.onrender.com",
    ],
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
    
    return HealthCheckResponse(
        status="healthy" if all([database_connected, fhir_server_reachable]) else "degraded",
        service="Smart EHR Backend",
        timestamp=datetime.utcnow(),
        database_connected=database_connected,
        vector_db_initialized=False,  # Deprecated
        fhir_server_reachable=fhir_server_reachable
    )
# Include routers
app.include_router(patients.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(alzheimers.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(observations.router, prefix="/api")
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )
