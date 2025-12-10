# Smart EHR Backend System
A comprehensive backend system that integrates SQL database, Vector Database (FAISS), and RAG pipeline with the existing FHIR server for the Smart EHR system.
## Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   Patients   │    Files     │    Models    │   Queries    │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
└────┬──────────────┬──────────────┬──────────────┬──────────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│   SQL   │  │  Vector  │  │   FHIR   │  │     RAG      │
│Database │  │    DB    │  │  Server  │  │   Service    │
│         │  │ (FAISS)  │  │          │  │              │
└─────────┘  └──────────┘  └──────────┘  └──────────────┘
```
## Key Features
### 1. **SQL Database Layer**
- **Patients**: Demographics, FHIR ID, NFC card ID linkage
- **Files**: Metadata for uploaded documents (PDFs, images, notes)
- **Parameters**: Clinically relevant structured data only
- **Model Results**: Disease model execution history
- **Vector Documents**: Tracking of embedded document chunks
### 2. **Vector Database (FAISS)**
- Semantic search over patient documents
- Stores embeddings of document chunks
- Enables RAG-based parameter extraction
- Patient-scoped search capabilities
### 3. **RAG Pipeline**
- Extracts missing model parameters from unstructured documents
- Answers natural language queries about patients
- Pattern-based numeric value extraction
- Confidence scoring for extracted values
### 4. **FHIR Integration**
- Fetches patient demographics and clinical data
- Extracts vital signs and lab results using LOINC codes
- Syncs structured parameters to SQL database
- Maintains FHIR as authoritative clinical source
### 5. **Disease Models**
- Alzheimer's Risk Model (example)
- Diabetes Risk Model (example)
- Extensible architecture for new models
- Automatic parameter fetching from SQL/FHIR/RAG
## Data Flow
### A. Patient Registration
```
1. Create patient → SQL entry
2. Link to FHIR ID
3. Optionally link to NFC card ID
4. Fetch demographics from FHIR
```
### B. File Upload
```
1. Upload file → Save to storage
2. Create metadata in SQL (files table)
3. Background worker processes file:
   - Extract text (PDF/OCR/DOCX)
   - Chunk text with overlap
   - Generate embeddings
   - Store in vector DB
   - Mark as processed in SQL
```
### C. Parameter Extraction (Priority Order)
```
1. Check SQL database (cached values)
2. If missing → Query FHIR server
3. If still missing → RAG extraction from documents
4. Store extracted values in SQL for future use
```
### D. Model Execution
```
1. Get required parameters for model
2. Fetch from SQL/FHIR/RAG (automatic)
3. Run disease model
4. Store input + output in model_results table
5. Return results with confidence scores
```
### E. Natural Language Queries
```
1. User asks: "What was the patient's MMSE last year?"
2. Semantic search in vector DB
3. Extract relevant information
4. Return answer with sources
```
## Installation
### Prerequisites
- Python 3.9+
- FHIR server running (default: http://localhost:8000)
- Optional: Tesseract OCR for image text extraction
### Setup
1. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```
2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```
3. **Initialize database**:
```bash
# Database will be created automatically on first run
# For migrations, use Alembic (optional)
```
4. **Download embedding model** (happens automatically on first run):
```bash
# The sentence-transformers model will be downloaded
# Model: sentence-transformers/all-MiniLM-L6-v2 (~90MB)
```
## Running the Backend
### Start the API Server
```bash
cd backend
python -m app.main
```
The API will be available at:
- **API**: http://localhost:8001
- **Docs**: http://localhost:8001/docs
- **Health**: http://localhost:8001/health
### Start the File Processing Worker (Optional)
```bash
cd backend
python -m app.workers.file_worker
```
This background worker processes uploaded files continuously.
## API Endpoints
### Patients
- `POST /api/patients/` - Register new patient
- `GET /api/patients/{patient_id}` - Get patient details
- `GET /api/patients/` - List all patients
- `PUT /api/patients/{patient_id}` - Update patient
- `DELETE /api/patients/{patient_id}` - Delete patient
- `POST /api/patients/{patient_id}/sync-fhir` - Sync from FHIR
- `GET /api/patients/by-nfc/{nfc_card_id}` - Get by NFC card
- `GET /api/patients/by-fhir/{fhir_id}` - Get by FHIR ID
### Files
- `POST /api/files/upload` - Upload file
- `GET /api/files/{file_id}` - Get file metadata
- `GET /api/files/patient/{patient_id}` - List patient files
- `DELETE /api/files/{file_id}` - Delete file
- `POST /api/files/{file_id}/reprocess` - Reprocess file
- `POST /api/files/process-unprocessed` - Process all pending files
- `GET /api/files/stats/processing-status` - Get processing stats
### Models
- `GET /api/models/available` - List available models
- `GET /api/models/{model_name}/info` - Get model info
- `POST /api/models/execute` - Execute disease model
- `GET /api/models/results/{result_id}` - Get model result
- `GET /api/models/results/patient/{patient_id}` - Get patient results
- `DELETE /api/models/results/{result_id}` - Delete result
- `GET /api/models/stats/patient/{patient_id}` - Get patient stats
### Queries
- `POST /api/queries/natural-language` - Natural language query
- `POST /api/queries/parameters` - Query parameters
- `GET /api/queries/parameters/{patient_id}/latest` - Latest parameters
- `GET /api/queries/parameters/{patient_id}/{param}/history` - Parameter history
- `POST /api/queries/rag/search` - Semantic search
- `POST /api/queries/parameters/extract/{patient_id}/{param}` - Extract parameter
- `GET /api/queries/stats/parameters/{patient_id}` - Parameter stats
- `GET /api/queries/vector-db/stats` - Vector DB stats
## Database Schema
### SQL Tables
**patients**
- `id` (PK): UUID
- `fhir_id`: Link to FHIR server
- `nfc_card_id`: Link to NFC card
- `first_name`, `last_name`, `date_of_birth`, `gender`
- `created_at`, `updated_at`
**files**
- `id` (PK): UUID
- `patient_id` (FK): References patients
- `filename`, `file_type`, `category`
- `file_path`, `file_size`
- `processed`, `processing_error`
- `uploaded_at`, `processed_at`
**parameters**
- `id` (PK): UUID
- `patient_id` (FK): References patients
- `parameter_name`: e.g., "mmse", "glucose"
- `value`: Numeric value
- `unit`: e.g., "mg/dL"
- `source`: FHIR / FILE / MANUAL / RAG
- `source_id`: Reference to source
- `timestamp`, `created_at`
**model_results**
- `id` (PK): UUID
- `patient_id` (FK): References patients
- `model_name`, `model_version`
- `input_parameters`: JSON
- `output_results`: JSON
- `execution_time_ms`, `confidence_score`
- `executed_at`
**vector_documents**
- `id` (PK): UUID
- `patient_id` (FK): References patients
- `file_id` (FK): References files
- `chunk_index`: Position in document
- `chunk_text`: Text content
- `vector_id`: Index in FAISS
- `created_at`
## Adding New Disease Models
To add a new disease model:
1. **Create model class** in `app/services/model_runner.py`:
```python
class MyDiseaseModel(DiseaseModel):
    def __init__(self):
        super().__init__(name="my_disease", version="1.0")
    
    def get_required_parameters(self) -> List[str]:
        return ["param1", "param2", "param3"]
    
    def run(self, parameters: Dict[str, float]) -> Dict[str, Any]:
        # Your model logic here
        risk_score = calculate_risk(parameters)
        
        return {
            "risk_score": risk_score,
            "risk_level": "Low" | "Moderate" | "High",
            "recommendations": ["..."]
        }
```
2. **Register model** in `ModelRunner.__init__`:
```python
self.models["my_disease"] = MyDiseaseModel()
```
3. **Use the model**:
```bash
POST /api/models/execute
{
  "patient_id": "...",
  "model_name": "my_disease"
}
```
The system will automatically fetch required parameters!
## Configuration
Key environment variables in `.env`:
```bash
# Server
HOST=0.0.0.0
PORT=8001
# Database
DATABASE_URL=sqlite:///./backend.db
# FHIR Server
FHIR_SERVER_URL=http://localhost:8000
# Vector DB
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=50
# File Storage
FILE_STORAGE_PATH=./storage/files
MAX_FILE_SIZE_MB=50
```
## Integration with Frontend
The frontend can integrate with this backend by:
1. **Patient lookup**: Use NFC card ID or FHIR ID
2. **File upload**: Upload medical documents
3. **Run models**: Execute disease prediction models
4. **Query data**: Ask natural language questions
5. **View history**: See model results and parameter trends
Example frontend integration:
```javascript
// Register patient
const patient = await fetch('http://localhost:8001/api/patients/', {
  method: 'POST',
  body: JSON.stringify({
    fhir_id: 'patient-123',
    nfc_card_id: 'card-456'
  })
});
// Upload file
const formData = new FormData();
formData.append('patient_id', patientId);
formData.append('category', 'lab_report');
formData.append('file', fileBlob);
await fetch('http://localhost:8001/api/files/upload', {
  method: 'POST',
  body: formData
});
// Run Alzheimer's model
const result = await fetch('http://localhost:8001/api/models/execute', {
  method: 'POST',
  body: JSON.stringify({
    patient_id: patientId,
    model_name: 'alzheimer_risk'
  })
});
```
## System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB+ for documents and embeddings
- **Python**: 3.9 or higher
## Troubleshooting
### FHIR Server Connection Failed
- Ensure FHIR server is running on configured URL
- Check `FHIR_SERVER_URL` in `.env`
### Vector DB Not Initialized
- First run downloads embedding model (~90MB)
- Ensure internet connection for initial setup
### File Processing Errors
- Check file format is supported (PDF, images, DOCX, TXT)
- For images, ensure Tesseract OCR is installed
- Check file size limits
### Missing Parameters
- Sync from FHIR: `POST /api/patients/{id}/sync-fhir`
- Upload relevant documents
- Manually add parameters via API
## Future Enhancements
- [ ] PostgreSQL support for production
- [ ] Redis-based task queue for file processing
- [ ] Advanced LLM integration for better NL queries
- [ ] Real-time parameter monitoring
- [ ] Multi-modal embeddings (images + text)
- [ ] Federated learning for privacy-preserving models
- [ ] FHIR write-back capabilities
- [ ] Audit logging and compliance features
## License
This project is part of the Smart EHR System.
## Support
For issues or questions, please refer to the main Smart EHR System repository.
