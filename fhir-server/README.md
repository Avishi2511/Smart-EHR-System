# Python FHIR Server

A FHIR R4 compliant server built with FastAPI and SQLAlchemy, designed to integrate with the Smart-EHR-System.

## Features

- **FHIR R4 Compliance**: Supports standard FHIR resources and operations
- **RESTful API**: Full CRUD operations for FHIR resources
- **Search Capabilities**: Advanced search parameters for different resource types
- **Database Support**: SQLite (development) and PostgreSQL (production)
- **CORS Enabled**: Ready for web application integration
- **Auto Documentation**: Interactive API docs with Swagger UI
- **Data Validation**: Built-in FHIR resource validation

## Supported FHIR Resources

- Patient
- Observation
- Condition
- Encounter
- MedicationRequest
- Procedure
- AllergyIntolerance
- Immunization

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Navigate to the FHIR server directory:**
   ```bash
   cd fhir-server
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

The server uses SQLite by default for easy setup. For production, you can configure PostgreSQL in the `.env` file:

```env
# For PostgreSQL (optional)
DATABASE_URL=postgresql://fhir_user:fhir_password@localhost:5432/fhir_db

# For SQLite (default)
DATABASE_URL=sqlite:///./fhir.db
```

### Running the Server

1. **Start the FHIR server:**
   ```bash
   python -m app.main
   ```

2. **The server will start on http://localhost:8000**

3. **Access the API documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Loading Sample Data

To populate the server with sample data:

```bash
python load_sample_data.py
```

This will create sample patients, observations, conditions, encounters, and medication requests.

## API Endpoints

### Core FHIR Operations

- `GET /metadata` - FHIR CapabilityStatement
- `GET /health` - Server health check
- `POST /{resourceType}` - Create a resource
- `GET /{resourceType}/{id}` - Read a resource
- `PUT /{resourceType}/{id}` - Update a resource
- `DELETE /{resourceType}/{id}` - Delete a resource
- `GET /{resourceType}` - Search resources

### Search Parameters

#### Patient Search
- `name` - Search by name (given or family)
- `family` - Search by family name
- `given` - Search by given name
- `birthdate` - Search by birth date
- `gender` - Search by gender

#### Observation Search
- `patient` - Search by patient reference
- `code` - Search by observation code
- `date` - Search by observation date

#### Condition Search
- `patient` - Search by patient reference
- `code` - Search by condition code

### Example API Calls

**Create a Patient:**
```bash
curl -X POST http://localhost:8000/Patient \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "name": [{"given": ["John"], "family": "Doe"}],
    "gender": "male",
    "birthDate": "1980-01-15"
  }'
```

**Search Patients:**
```bash
curl "http://localhost:8000/Patient?name=John"
```

**Get a Specific Patient:**
```bash
curl http://localhost:8000/Patient/patient-001
```

## Integration with Smart-EHR-System

To integrate with the Smart-EHR-System:

1. **Update the Smart-EHR-System .env file:**
   ```env
   VITE_FHIR_SERVER_URL=http://localhost:8000
   VITE_AUTH_REQUIRED=false
   VITE_LAUNCH_PARAM_CONFIG=default
   ```

2. **Update the fhirApi.ts file** to use real HTTP requests instead of mock data.

3. **Start both servers:**
   ```bash
   # Terminal 1: Start FHIR server
   cd fhir-server
   python -m app.main
   
   # Terminal 2: Start React app
   cd ..
   npm run dev
   ```

## Database Schema

The server uses a simple but effective schema:

```sql
CREATE TABLE fhir_resources (
    id VARCHAR PRIMARY KEY,
    resource_type VARCHAR(50) NOT NULL,
    version_id VARCHAR DEFAULT '1',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Development

### Project Structure
```
fhir-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── crud.py              # Database operations
│   └── api/
│       ├── __init__.py
│       └── fhir.py          # FHIR endpoints
├── requirements.txt
├── .env
├── load_sample_data.py
└── README.md
```

### Adding New Resource Types

1. Add the resource class import in `app/api/fhir.py`
2. Add it to the `SUPPORTED_RESOURCES` dictionary
3. Add search parameters in the `search_resources` function in `app/crud.py`

### Testing

You can test the API using:
- The interactive docs at http://localhost:8000/docs
- curl commands
- Postman or similar API testing tools
- The sample data loading script

## Production Deployment

For production deployment:

1. **Set up PostgreSQL:**
   ```bash
   # Install PostgreSQL and create database
   createdb fhir_db
   createuser fhir_user
   ```

2. **Update .env for production:**
   ```env
   DATABASE_URL=postgresql://fhir_user:password@localhost:5432/fhir_db
   DEBUG=False
   ```

3. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the fhir-server directory and have activated the virtual environment

2. **Database connection errors**: Check your DATABASE_URL in the .env file

3. **CORS errors**: The server is configured to allow requests from localhost:5173 and localhost:3000

4. **Port conflicts**: Change the PORT in .env if 8000 is already in use

### Logs

The server logs are displayed in the console. For production, configure proper logging.

## License

This project is part of the Smart-EHR-System and follows the same licensing terms.
