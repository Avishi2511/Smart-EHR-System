import sys
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models.sql_models import File

db = SessionLocal()
files = db.query(File).order_by(File.uploaded_at.desc()).limit(5).all()

print('Recent uploaded files:')
print('=' * 80)
for f in files:
    print(f'\nFilename: {f.filename}')
    print(f'Uploaded: {f.uploaded_at}')
    print(f'Processed: {f.processed}')
    print(f'Processing Error: {f.processing_error}')
    print(f'File Path: {f.file_path}')
    print('-' * 80)

db.close()
