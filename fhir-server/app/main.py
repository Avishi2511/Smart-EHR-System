from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Base
from app.api import fhir
import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Python FHIR Server",
    description="A FHIR R4 compliant server built with FastAPI and SQLAlchemy",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React frontend
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Python FHIR Server is running",
        "version": "1.0.0",
        "fhir_version": "4.0.1"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "FHIR Server"}

@app.get("/metadata")
async def get_capability_statement():
    """FHIR CapabilityStatement endpoint"""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "publisher": "Custom Python FHIR Server",
        "kind": "instance",
        "software": {
            "name": "Python FHIR Server",
            "version": "1.0.0"
        },
        "implementation": {
            "description": "A FHIR R4 server implementation using FastAPI"
        },
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "documentation": "Main FHIR endpoint for RESTful interactions",
            "security": {
                "cors": True,
                "description": "CORS enabled for web applications"
            },
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "birthdate", "type": "date"},
                        {"name": "gender", "type": "token"}
                    ]
                },
                {
                    "type": "Observation",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "code", "type": "token"},
                        {"name": "date", "type": "date"}
                    ]
                },
                {
                    "type": "Condition",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "code", "type": "token"}
                    ]
                },
                {
                    "type": "Encounter",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ]
                },
                {
                    "type": "MedicationRequest",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ]
                },
                {
                    "type": "Procedure",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ]
                },
                {
                    "type": "AllergyIntolerance",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ]
                },
                {
                    "type": "Immunization",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ]
                },
                {
                    "type": "Practitioner",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "name", "type": "string"},
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"}
                    ]
                }
            ]
        }]
    }

# Include FHIR routes
app.include_router(fhir.router, tags=["FHIR"])

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
