# Smart EHR Backend Architecture Documentation
## System Overview
The Smart EHR Backend is a comprehensive medical data management system that integrates:
- **SQL Database**: For structured clinical parameters
- **Vector Database (FAISS)**: For unstructured document embeddings
- **RAG Pipeline**: For intelligent parameter extraction
- **FHIR Integration**: For clinical data interoperability
## Design Principles
### 1. Clean SQL Schema
- **Only clinically relevant structured data** is stored in SQL
- No bloated text storage in relational tables
- Parameters table stores extracted facts, not raw documents
- Efficient querying and indexing
### 2. Unstructured Content in Vector DB
- Full text of documents remains retrievable
- Semantic search capabilities
- Patient-scoped embeddings
- Scalable to millions of documents
### 3. RAG-First Parameter Extraction
- Missing parameters automatically extracted from documents
- Confidence scoring for extracted values
- Fallback to FHIR when documents don't contain data
- Extracted values cached in SQL
### 4. Multi-Disease Support
- Extensible model architecture
- Each model declares required parameters
- Automatic parameter fetching
- Historical model results tracking
### 5. Lifelong Patient Records
- Supports decades of patient data
- Efficient time-series parameter storage
- Document versioning and tracking
- Audit trail for all data sources
## Component Architecture
### SQL Database Layer
```
┌─────────────────────────────────────────────────────────┐
│                     SQL Database                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   patients   │  │    files     │  │  parameters  │ │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤ │
│  │ id           │  │ id           │  │ id           │ │
│  │ fhir_id      │  │ patient_id   │  │ patient_id   │ │
│  │ nfc_card_id  │  │ filename     │  │ param_name   │ │
│  │ first_name   │  │ file_type    │  │ value        │ │
│  │ last_name    │  │ category     │  │ unit         │ │
│  │ dob          │  │ file_path    │  │ source       │ │
│  │ gender       │  │ processed    │  │ timestamp    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │model_results │  │    vector_documents          │   │
│  ├──────────────┤  ├──────────────────────────────┤   │
│  │ id           │  │ id                           │   │
│  │ patient_id   │  │ patient_id                   │   │
│  │ model_name   │  │ file_id                      │   │
│  │ input_params │  │ chunk_index                  │   │
│  │ output_res   │  │ chunk_text                   │   │
│  │ executed_at  │  │ vector_id (FAISS index)      │   │
│  └──────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```
**Key Design Decisions:**
- `parameters` table stores only extracted facts (e.g., "glucose: 110 mg/dL")
- `files` table stores metadata only, not file content
- `vector_documents` tracks which chunks are in FAISS
- `model_results` stores complete input/output as JSON for reproducibility
### Vector Database Layer
```
┌─────────────────────────────────────────────────────────┐
│              Vector Database (FAISS)                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Embedding Model: sentence-transformers/all-MiniLM-L6-v2│
│  Dimension: 384                                          │
│  Index Type: IndexFlatL2 (exact search)                 │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Document Processing Pipeline                   │    │
│  ├────────────────────────────────────────────────┤    │
│  │  1. Extract text (PDF/OCR/DOCX)                │    │
│  │  2. Chunk with overlap (500 chars, 50 overlap) │    │
│  │  3. Generate embeddings                         │    │
│  │  4. Store in FAISS index                        │    │
│  │  5. Link to SQL (vector_documents table)       │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Storage:                                                │
│  - faiss.index: Binary FAISS index                      │
│  - metadata.pkl: Chunk metadata (patient_id, file_id)   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
**Key Design Decisions:**
- Chunking with overlap prevents information loss at boundaries
- Patient ID stored in metadata for scoped search
- Exact search (L2 distance) for accuracy over speed
- Persistent storage for index and metadata
### RAG Service Layer
```
┌─────────────────────────────────────────────────────────┐
│                    RAG Service                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Parameter Extraction Pipeline                  │    │
│  ├────────────────────────────────────────────────┤    │
│  │  1. Semantic search for parameter name         │    │
│  │  2. Retrieve top-K relevant chunks              │    │
│  │  3. Pattern matching for numeric values         │    │
│  │  4. Confidence scoring                          │    │
│  │  5. Store in SQL if confident                   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Natural Language Query Pipeline                │    │
│  ├────────────────────────────────────────────────┤    │
│  │  1. Embed query                                 │    │
│  │  2. Semantic search                             │    │
│  │  3. Retrieve context                            │    │
│  │  4. Format answer with sources                  │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
**Pattern Matching Examples:**
- "MMSE: 24" → extracts 24
- "Blood glucose is 110 mg/dL" → extracts 110
- "HbA1c = 6.2%" → extracts 6.2
### FHIR Integration Layer
```
┌─────────────────────────────────────────────────────────┐
│                  FHIR Integration                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  FHIR Server: http://localhost:8000                     │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Supported Resources                            │    │
│  ├────────────────────────────────────────────────┤    │
│  │  - Patient (demographics)                       │    │
│  │  - Observation (vital signs, lab results)       │    │
│  │  - Condition (diagnoses)                        │    │
│  │  - MedicationRequest (prescriptions)            │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  LOINC Code Mapping                             │    │
│  ├────────────────────────────────────────────────┤    │
│  │  8480-6  → systolic_bp                          │    │
│  │  8462-4  → diastolic_bp                         │    │
│  │  2339-0  → glucose                              │    │
│  │  4548-4  → hba1c                                │    │
│  │  ... (20+ mappings)                             │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
**Integration Flow:**
1. Patient registered with FHIR ID
2. Demographics fetched from FHIR
3. Clinical parameters synced on demand
4. FHIR remains authoritative source
5. SQL caches for performance
### Model Execution Layer
```
┌─────────────────────────────────────────────────────────┐
│                  Model Runner                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Execution Pipeline                             │    │
│  ├────────────────────────────────────────────────┤    │
│  │  1. Get required parameters for model           │    │
│  │  2. Check SQL database                          │    │
│  │  3. If missing → Query FHIR                     │    │
│  │  4. If still missing → RAG extraction           │    │
│  │  5. Run model with parameters                   │    │
│  │  6. Store results in model_results              │    │
│  │  7. Return results + metadata                   │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  Available Models:                                       │
│  ┌────────────────────────────────────────────────┐    │
│  │  alzheimer_risk                                 │    │
│  │  - age, mmse, apoe4_status                      │    │
│  │  - education_years, hippocampal_volume          │    │
│  │  - amyloid_beta                                 │    │
│  └────────────────────────────────────────────────┘    │
│  ┌────────────────────────────────────────────────┐    │
│  │  diabetes_risk                                  │    │
│  │  - age, bmi, glucose, hba1c                     │    │
│  │  - systolic_bp, family_history_diabetes         │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```
## Data Flow Diagrams
### File Upload Flow
```
User uploads PDF
       │
       ▼
┌──────────────┐
│ Save to disk │
│ /storage/... │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Create file      │
│ record in SQL    │
│ (processed=False)│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Extract text     │
│ (PDF/OCR/DOCX)   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Chunk text       │
│ (500 chars,      │
│  50 overlap)     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Generate         │
│ embeddings       │
│ (384-dim)        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Store in FAISS   │
│ index            │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Create vector_   │
│ documents records│
│ in SQL           │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Mark file as     │
│ processed=True   │
└──────────────────┘
```
### Parameter Extraction Flow
```
Model needs "glucose"
       │
       ▼
┌──────────────────┐
│ Check SQL DB     │
│ parameters table │
└──────┬───────────┘
       │
       ├─ Found ──────────────┐
       │                      │
       └─ Not Found           │
              │               │
              ▼               │
       ┌──────────────┐       │
       │ Query FHIR   │       │
       │ Observations │       │
       └──────┬───────┘       │
              │               │
              ├─ Found ───────┤
              │               │
              └─ Not Found    │
                     │        │
                     ▼        │
              ┌──────────────┐│
              │ RAG Search   ││
              │ in vector DB ││
              └──────┬───────┘│
                     │        │
                     ├─ Found │
                     │        │
                     └─ Not   │
                        Found │
                              │
                              ▼
                       ┌──────────────┐
                       │ Store in SQL │
                       │ for future   │
                       └──────────────┘
```
### Model Execution Flow
```
POST /api/models/execute
{
  "patient_id": "...",
  "model_name": "alzheimer_risk"
}
       │
       ▼
┌──────────────────────┐
│ Get model instance   │
│ AlzheimerRiskModel() │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Get required params: │
│ [age, mmse, apoe4,   │
│  education, ...]     │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Fetch each param     │
│ (SQL→FHIR→RAG)       │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Run model.run()      │
│ with parameters      │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Calculate risk score │
│ Generate recommends  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Store in             │
│ model_results table  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Return results       │
│ {risk_score: 0.65,   │
│  risk_level: "High"} │
└──────────────────────┘
```
## Scalability Considerations
### Database Scaling
- **SQLite**: Good for development and small deployments
- **PostgreSQL**: Recommended for production
- **Partitioning**: Partition `parameters` by patient_id or timestamp
- **Indexing**: Composite indexes on (patient_id, parameter_name, timestamp)
### Vector Database Scaling
- **Current**: FAISS IndexFlatL2 (exact search)
- **For scale**: Use IndexIVFFlat or IndexHNSW for approximate search
- **Distributed**: Consider Milvus or Weaviate for multi-node deployment
- **Sharding**: Shard by patient_id for horizontal scaling
### File Storage Scaling
- **Current**: Local filesystem
- **For scale**: Use S3-compatible object storage
- **CDN**: Serve frequently accessed files via CDN
- **Compression**: Compress old files to save space
### Model Execution Scaling
- **Current**: Synchronous execution
- **For scale**: Use Celery + Redis for async execution
- **Batching**: Batch model runs for multiple patients
- **Caching**: Cache model results with TTL
## Security Considerations
### Data Protection
- **Encryption at rest**: Encrypt database and file storage
- **Encryption in transit**: Use HTTPS/TLS
- **Access control**: Implement role-based access control (RBAC)
- **Audit logging**: Log all data access and modifications
### HIPAA Compliance
- **PHI protection**: Encrypt all patient health information
- **Access logs**: Maintain comprehensive audit trails
- **Data retention**: Implement retention policies
- **Breach notification**: Automated breach detection
### API Security
- **Authentication**: Implement OAuth2/JWT
- **Rate limiting**: Prevent abuse
- **Input validation**: Validate all inputs
- **CORS**: Restrict origins
## Performance Optimization
### Database Optimization
- **Connection pooling**: Reuse database connections
- **Query optimization**: Use indexes effectively
- **Batch operations**: Bulk insert parameters
- **Caching**: Cache frequently accessed data
### Vector Search Optimization
- **Index selection**: Choose appropriate FAISS index type
- **Dimensionality reduction**: Consider PCA for large embeddings
- **Quantization**: Use product quantization for compression
- **GPU acceleration**: Use FAISS GPU for faster search
### API Optimization
- **Async operations**: Use async/await throughout
- **Response compression**: Enable gzip compression
- **Pagination**: Paginate large result sets
- **Caching**: Use Redis for response caching
## Monitoring and Observability
### Metrics to Track
- **API latency**: Response times for each endpoint
- **Database performance**: Query execution times
- **Vector search latency**: Search times in FAISS
- **Model execution time**: Time per model run
- **File processing rate**: Files processed per hour
- **Error rates**: 4xx and 5xx errors
### Logging
- **Structured logging**: Use JSON format
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Correlation IDs**: Track requests across services
- **Sensitive data**: Never log PHI
### Alerting
- **Health check failures**: Alert on /health endpoint failures
- **High error rates**: Alert on error rate spikes
- **Slow queries**: Alert on slow database queries
- **Disk space**: Alert on low disk space
## Future Enhancements
### Short Term
1. **PostgreSQL migration**: Move from SQLite to PostgreSQL
2. **Async file processing**: Implement Celery workers
3. **Advanced NLP**: Integrate GPT for better query answering
4. **API authentication**: Add OAuth2/JWT
### Medium Term
1. **Multi-modal embeddings**: Embed images + text together
2. **Real-time monitoring**: Live parameter dashboards
3. **Federated learning**: Privacy-preserving model training
4. **FHIR write-back**: Update FHIR from backend
### Long Term
1. **Distributed deployment**: Multi-region deployment
2. **AI-powered insights**: Automated clinical insights
3. **Predictive analytics**: Early warning systems
4. **Integration hub**: Connect to multiple EHR systems
## Conclusion
This architecture provides a solid foundation for a scalable, maintainable, and extensible medical data management system. The separation of structured (SQL) and unstructured (Vector DB) data, combined with intelligent RAG-based extraction, enables both efficient querying and comprehensive document search.
The system is designed to grow with the organization, supporting lifelong patient records, multiple disease models, and integration with existing clinical systems through FHIR.