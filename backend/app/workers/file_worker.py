"""
Background worker for processing unprocessed files
This script can be run as a separate process to continuously
process files that have been uploaded but not yet embedded.
Usage:
    python -m app.workers.file_worker
"""
import asyncio
import time
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.file_processor import file_processor
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
async def process_files_worker(interval: int = 60):
    """
    Background worker that processes unprocessed files
    
    Args:
        interval: Time in seconds between processing runs
    """
    logger.info(f"Starting file processing worker (interval: {interval}s)")
    
    while True:
        try:
            db = SessionLocal()
            
            logger.info("Checking for unprocessed files...")
            count = await file_processor.process_unprocessed_files(db)
            
            if count > 0:
                logger.info(f"Processed {count} files")
            else:
                logger.debug("No unprocessed files found")
            
            db.close()
            
        except Exception as e:
            logger.error(f"Error in file processing worker: {e}")
        
        # Wait before next iteration
        await asyncio.sleep(interval)
async def main():
    """Main entry point for the worker"""
    try:
        await process_files_worker(interval=60)
    except KeyboardInterrupt:
        logger.info("File processing worker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in file processing worker: {e}")
if __name__ == "__main__":
    asyncio.run(main())
