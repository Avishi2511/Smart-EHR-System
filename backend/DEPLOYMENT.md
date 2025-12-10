# Deployment Guide - Smart EHR Backend
This guide covers deploying the Smart EHR Backend to production.
## Table of Contents
1. [Development Setup](#development-setup)
2. [Production Deployment](#production-deployment)
3. [Database Migration](#database-migration)
4. [Security Hardening](#security-hardening)
5. [Monitoring](#monitoring)
6. [Backup and Recovery](#backup-and-recovery)
## Development Setup
### Local Development
```bash
# Clone repository
cd Smart-EHR-System/backend
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Configure environment
cp .env.example .env
# Edit .env with your settings
# Run development server
python -m app.main
```
### Docker Development (Optional)
```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy application
COPY . .
# Create storage directories
RUN mkdir -p storage/files storage/vector_db
# Expose port
EXPOSE 8001
# Run application
CMD ["python", "-m", "app.main"]
```
```bash
# Build and run
docker build -t smart-ehr-backend .
docker run -p 8001:8001 -v $(pwd)/storage:/app/storage smart-ehr-backend
```
## Production Deployment
### Prerequisites
1. **Server Requirements**
   - Ubuntu 20.04+ or similar Linux distribution
   - 4GB+ RAM
   - 2+ CPU cores
   - 50GB+ disk space
   - Python 3.9+
2. **External Services**
   - PostgreSQL 13+ (recommended over SQLite)
   - Redis (for background tasks)
   - FHIR server
   - Reverse proxy (Nginx)
### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y
# Install dependencies
sudo apt install -y python3.9 python3-pip python3-venv \
    postgresql postgresql-contrib redis-server \
    tesseract-ocr nginx supervisor
# Create application user
sudo useradd -m -s /bin/bash smartehr
sudo su - smartehr
```
### Step 2: Application Setup
```bash
# Clone repository
git clone <repository-url>
cd Smart-EHR-System/backend
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
# Create storage directories
mkdir -p storage/files storage/vector_db
chmod 755 storage
```
### Step 3: Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql
```
```sql
CREATE DATABASE smartehr;
CREATE USER smartehr WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE smartehr TO smartehr;
\q
```
Update `.env`:
```bash
DATABASE_URL=postgresql://smartehr:secure_password_here@localhost/smartehr
```
### Step 4: Environment Configuration
```bash
# Production .env
HOST=127.0.0.1
PORT=8001
DEBUG=False
DATABASE_URL=postgresql://smartehr:secure_password@localhost/smartehr
FHIR_SERVER_URL=http://localhost:8000
FHIR_SERVER_TIMEOUT=30
VECTOR_DB_PATH=/home/smartehr/Smart-EHR-System/backend/storage/vector_db
FILE_STORAGE_PATH=/home/smartehr/Smart-EHR-System/backend/storage/files
MAX_FILE_SIZE_MB=50
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```
### Step 5: Gunicorn Configuration
Create `gunicorn_config.py`:
```python
import multiprocessing
# Server socket
bind = "127.0.0.1:8001"
backlog = 2048
# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2
# Logging
accesslog = "/home/smartehr/logs/access.log"
errorlog = "/home/smartehr/logs/error.log"
loglevel = "info"
# Process naming
proc_name = "smartehr-backend"
# Server mechanics
daemon = False
pidfile = "/home/smartehr/smartehr.pid"
```
### Step 6: Supervisor Configuration
Create `/etc/supervisor/conf.d/smartehr-backend.conf`:
```ini
[program:smartehr-backend]
command=/home/smartehr/Smart-EHR-System/backend/venv/bin/gunicorn -c gunicorn_config.py app.main:app
directory=/home/smartehr/Smart-EHR-System/backend
user=smartehr
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/smartehr/logs/supervisor.log
environment=PATH="/home/smartehr/Smart-EHR-System/backend/venv/bin"
```
Create file worker config `/etc/supervisor/conf.d/smartehr-worker.conf`:
```ini
[program:smartehr-worker]
command=/home/smartehr/Smart-EHR-System/backend/venv/bin/python -m app.workers.file_worker
directory=/home/smartehr/Smart-EHR-System/backend
user=smartehr
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/smartehr/logs/worker.log
environment=PATH="/home/smartehr/Smart-EHR-System/backend/venv/bin"
```
```bash
# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smartehr-backend
sudo supervisorctl start smartehr-worker
```
### Step 7: Nginx Configuration
Create `/etc/nginx/sites-available/smartehr-backend`:
```nginx
upstream smartehr_backend {
    server 127.0.0.1:8001;
}
server {
    listen 80;
    server_name api.yourdomain.com;
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    # File upload size
    client_max_body_size 50M;
    # Proxy settings
    location / {
        proxy_pass http://smartehr_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    # Health check endpoint
    location /health {
        proxy_pass http://smartehr_backend/health;
        access_log off;
    }
}
```
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/smartehr-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```
### Step 8: SSL Certificate (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx
# Obtain certificate
sudo certbot --nginx -d api.yourdomain.com
# Auto-renewal is configured automatically
```
## Database Migration
### From SQLite to PostgreSQL
```bash
# Export data from SQLite
python -c "
from app.database import engine
import pandas as pd
# Export each table
for table in ['patients', 'files', 'parameters', 'model_results', 'vector_documents']:
    df = pd.read_sql_table(table, engine)
    df.to_csv(f'{table}.csv', index=False)
"
# Update .env to PostgreSQL
DATABASE_URL=postgresql://smartehr:password@localhost/smartehr
# Import data
python -c "
from app.database import engine
import pandas as pd
for table in ['patients', 'files', 'parameters', 'model_results', 'vector_documents']:
    df = pd.read_csv(f'{table}.csv')
    df.to_sql(table, engine, if_exists='append', index=False)
"
```
## Security Hardening
### 1. Environment Variables
```bash
# Never commit .env to git
# Use environment-specific .env files
# Store secrets in secret management system (AWS Secrets Manager, HashiCorp Vault)
```
### 2. API Authentication
Add JWT authentication (future enhancement):
```python
# app/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
security = HTTPBearer()
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```
### 3. Database Security
```sql
-- Restrict database user permissions
REVOKE ALL ON DATABASE smartehr FROM PUBLIC;
GRANT CONNECT ON DATABASE smartehr TO smartehr;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO smartehr;
```
### 4. File Upload Security
```python
# Validate file types
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt'}
# Scan for malware (integrate with ClamAV)
import pyclamd
cd = pyclamd.ClamdUnixSocket()
scan_result = cd.scan_file(file_path)
```
### 5. Rate Limiting
```python
# Install slowapi
pip install slowapi
# Add to main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Apply to endpoints
@app.get("/api/patients/")
@limiter.limit("100/minute")
async def list_patients():
    ...
```
## Monitoring
### 1. Application Monitoring
```bash
# Install Prometheus client
pip install prometheus-fastapi-instrumentator
# Add to main.py
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```
### 2. Log Aggregation
```bash
# Use ELK Stack or similar
# Configure structured logging
# app/logging_config.py
import logging.config
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/smartehr/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
            "formatter": "json"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["file"]
    }
}
logging.config.dictConfig(LOGGING_CONFIG)
```
### 3. Health Checks
```bash
# Monitor /health endpoint
curl https://api.yourdomain.com/health
# Set up uptime monitoring (UptimeRobot, Pingdom, etc.)
```
## Backup and Recovery
### 1. Database Backup
```bash
# Create backup script
#!/bin/bash
# /home/smartehr/scripts/backup_db.sh
BACKUP_DIR="/home/smartehr/backups"
DATE=$(date +%Y%m%d_%H%M%S)
# Backup PostgreSQL
pg_dump -U smartehr smartehr > "$BACKUP_DIR/smartehr_$DATE.sql"
# Compress
gzip "$BACKUP_DIR/smartehr_$DATE.sql"
# Delete backups older than 30 days
find $BACKUP_DIR -name "smartehr_*.sql.gz" -mtime +30 -delete
```
```bash
# Add to crontab
crontab -e
0 2 * * * /home/smartehr/scripts/backup_db.sh
```
### 2. File Storage Backup
```bash
# Backup uploaded files
rsync -avz /home/smartehr/Smart-EHR-System/backend/storage/ \
    /backup/storage/
# Or use cloud storage
aws s3 sync /home/smartehr/Smart-EHR-System/backend/storage/ \
    s3://smartehr-backups/storage/
```
### 3. Vector Database Backup
```bash
# Backup FAISS index and metadata
cp storage/vector_db/faiss.index /backup/vector_db/
cp storage/vector_db/metadata.pkl /backup/vector_db/
```
### 4. Recovery
```bash
# Restore database
gunzip smartehr_20240101_020000.sql.gz
psql -U smartehr smartehr < smartehr_20240101_020000.sql
# Restore files
rsync -avz /backup/storage/ /home/smartehr/Smart-EHR-System/backend/storage/
# Restart services
sudo supervisorctl restart smartehr-backend
sudo supervisorctl restart smartehr-worker
```
## Performance Tuning
### 1. Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_parameters_patient_timestamp ON parameters(patient_id, timestamp DESC);
CREATE INDEX idx_files_patient_processed ON files(patient_id, processed);
CREATE INDEX idx_model_results_patient ON model_results(patient_id, executed_at DESC);
-- Analyze tables
ANALYZE patients;
ANALYZE parameters;
ANALYZE files;
```
### 2. Caching
```python
# Install Redis cache
pip install redis
# Add caching layer
from redis import Redis
cache = Redis(host='localhost', port=6379, db=0)
# Cache expensive queries
@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    # Check cache
    cached = cache.get(f"patient:{patient_id}")
    if cached:
        return json.loads(cached)
    
    # Fetch from database
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    
    # Cache result
    cache.setex(f"patient:{patient_id}", 3600, json.dumps(patient))
    
    return patient
```
### 3. Connection Pooling
```python
# Update database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```
## Troubleshooting
### Common Issues
1. **High memory usage**
   - Reduce worker count
   - Implement pagination
   - Clear old embeddings
2. **Slow queries**
   - Add database indexes
   - Optimize queries
   - Use caching
3. **File processing failures**
   - Check Tesseract installation
   - Verify file permissions
   - Check disk space
## Maintenance
### Regular Tasks
- **Daily**: Check logs for errors
- **Weekly**: Review disk usage, backup verification
- **Monthly**: Update dependencies, security patches
- **Quarterly**: Performance review, capacity planning
## Conclusion
This deployment guide provides a production-ready setup for the Smart EHR Backend. Follow security best practices, monitor your system, and maintain regular backups.
For support, refer to the main documentation or contact the development team.
