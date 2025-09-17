import os
import time
import logging
import schedule
import pandas as pd
from datetime import datetime
from allas_client import AllasClient
from data_processor import DataProcessor
import redis
import json

# Configure logging with detailed formatting for better debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataIngestService:
    """
    Main data ingestion service for CSC Allas integration.
    
    This service acts as the entry point for the data pipeline, responsible for:
    - Connecting to CSC Allas using Swift/OpenStack protocol
    - Discovering and downloading new data files
    - Coordinating with other services via Redis
    - Monitoring file changes and processing status
    
    The service runs on a scheduled basis (configurable interval) and ensures
    that only new or modified files are processed to avoid unnecessary work.
    """
    
    def __init__(self):
        """
        Initialize the data ingestion service with all required components.
        
        Sets up connections to:
        - CSC Allas (via AllasClient using Swift protocol)
        - Redis (for inter-service coordination)
        - Shared file system (for data exchange between containers)
        """
        # Initialize CSC Allas client with Swift/OpenStack authentication
        self.allas_client = AllasClient()
        
        # Data processor for handling different file formats (CSV, JSON, Excel)
        self.data_processor = DataProcessor()
        
        # Redis client for coordination between services (status tracking, file metadata)
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Shared volume path where processed files are stored for other services
        self.shared_data_path = "/shared/data"
        
        # Track last synchronization time to implement incremental sync
        self.last_sync_time = None
        
    def run_ingestion_cycle(self):
        """
        Execute a complete data ingestion cycle.
        
        This is the main orchestration method that:
        1. Connects to CSC Allas and lists available files
        2. Filters for new or modified files (incremental processing)
        3. Downloads and processes each new file
        4. Updates Redis with processing status
        5. Saves files to shared storage for downstream services
        
        Error handling ensures that failures with individual files don't
        stop the entire ingestion process.
        """
        try:
            logger.info("Starting data ingestion cycle - checking CSC Allas for new files")
            
            # Connect to CSC Allas and retrieve list of all available files
            # This uses Swift protocol to list objects in the configured container
            files = self.allas_client.list_files()
            logger.info(f"Found {len(files)} files in Allas container '{self.allas_client.container_name}'")
            
            # Filter files to process only new or updated ones (incremental processing)
            # This prevents reprocessing unchanged files and improves efficiency
            new_files = self._filter_new_files(files)
            if not new_files:
                logger.info("No new files to process - all files are up to date")
                return
                
            logger.info(f"Processing {len(new_files)} new or modified files")
            
            # Process each new file individually to allow for error isolation
            for file_info in new_files:
                try:
                    logger.info(f"Processing file: {file_info['name']}")
                    
                    # Download file content from CSC Allas using Swift protocol
                    # This retrieves the raw file data as bytes from the object storage
                    file_data = self.allas_client.download_file(file_info['name'])
                    logger.info(f"Downloaded {len(file_data)} bytes for {file_info['name']}")
                    
                    # Process the raw data using our data processor
                    # This handles format detection, parsing, and initial validation
                    processed_data = self.data_processor.process_raw_data(
                        file_data, 
                        file_info['name']
                    )
                    
                    # Save processed data to shared volume for other services to access
                    # The data-clean service will pick up these files for further processing
                    # File naming convention: "raw_" prefix indicates unprocessed data
                    output_path = os.path.join(
                        self.shared_data_path, 
                        f"raw_{file_info['name']}"
                    )
                    processed_data.to_csv(output_path, index=False)
                    logger.info(f"Saved processed data to: {output_path}")
                    
                    # Update Redis with file processing status for coordination
                    # Other services can check this status to know when files are ready
                    self._update_file_status(file_info['name'], 'ingested')
                    
                    logger.info(f"Successfully processed file: {file_info['name']}")
                    
                except Exception as e:
                    # Individual file errors shouldn't stop the entire process
                    # Log the error and mark the file status for investigation
                    logger.error(f"Error processing file {file_info['name']}: {str(e)}")
                    self._update_file_status(file_info['name'], 'error')
            
            # Update global synchronization timestamp after successful cycle
            # This helps implement incremental sync and track pipeline health
            self.last_sync_time = datetime.now()
            self._update_sync_status()
            
            logger.info("Data ingestion cycle completed successfully")
            
        except Exception as e:
            # Critical error in the main ingestion process
            logger.error(f"Critical error in ingestion cycle: {str(e)}")
            # Update Redis to indicate ingestion failure for monitoring
            self.redis_client.set('ingestion_status', 'error')
            
    def _filter_new_files(self, files):
        """
        Filter files to include only new or modified ones for incremental processing.
        
        This method implements incremental sync by comparing file modification times
        stored in Redis with the current file metadata from Allas. Only files that
        are new or have been modified since the last sync are returned for processing.
        
        Args:
            files: List of file metadata dictionaries from Allas
            
        Returns:
            List of files that need to be processed (new or modified)
        """
        new_files = []
        
        for file_info in files:
            # Create unique Redis key for this file's metadata
            file_key = f"file:{file_info['name']}"
            
            # Get the last known modification time from Redis
            last_modified = self.redis_client.get(file_key)
            
            # Include file if it's new (no Redis entry) or modified since last sync
            if (not last_modified or 
                file_info['last_modified'] != last_modified):
                new_files.append(file_info)
                logger.debug(f"File {file_info['name']} needs processing (new or modified)")
            else:
                logger.debug(f"File {file_info['name']} skipped (no changes)")
                
        return new_files
        
    def _update_file_status(self, filename, status):
        """
        Update file processing status in Redis for coordination between services.
        
        This method maintains two types of information in Redis:
        1. Processing status (ingested, error, cleaning, etc.)
        2. Last modification timestamp for incremental sync
        
        Args:
            filename: Name of the file being processed
            status: Current processing status ('ingested', 'error', etc.)
        """
        # Store current processing status for service coordination
        status_key = f"status:{filename}"
        self.redis_client.set(status_key, status)
        
        # Store file modification timestamp for incremental sync
        file_key = f"file:{filename}"
        self.redis_client.set(file_key, datetime.now().isoformat())
        
        logger.debug(f"Updated Redis status for {filename}: {status}")
        
    def _update_sync_status(self):
        """
        Update global synchronization status in Redis for pipeline monitoring.
        
        This provides a centralized way to track when the last successful
        ingestion cycle completed, which is useful for monitoring and
        troubleshooting the pipeline health.
        """
        sync_info = {
            'last_sync': self.last_sync_time.isoformat(),
            'status': 'completed',
            'service': 'data-ingest'
        }
        self.redis_client.set('sync_status', json.dumps(sync_info))
        logger.info(f"Updated global sync status: {sync_info['last_sync']}")
        
    def start(self):
        """
        Start the data ingestion service with scheduling.
        
        This method initializes the service by:
        1. Running an immediate ingestion cycle to process any existing files
        2. Setting up a recurring schedule for continuous operation
        3. Starting the main event loop to handle scheduled tasks
        
        The service runs continuously until interrupted, checking for new files
        at regular intervals (15 minutes by default, configurable via environment).
        """
        logger.info("Starting Data Ingest Service for CSC Allas integration")
        
        # Run initial ingestion cycle immediately upon startup
        # This ensures any existing files are processed right away
        logger.info("Running initial ingestion cycle...")
        self.run_ingestion_cycle()
        
        # Schedule regular ingestion cycles
        # Interval is configurable via environment variable PIPELINE_SCHEDULE_INGESTION
        schedule_interval = int(os.getenv('PIPELINE_SCHEDULE_INGESTION', 15))
        schedule.every(schedule_interval).minutes.do(self.run_ingestion_cycle)
        logger.info(f"Scheduled ingestion cycles every {schedule_interval} minutes")
        
        # Keep the service running with the scheduler
        # This main loop checks for scheduled tasks every minute and executes them
        # The service continues running until interrupted (Ctrl+C or container stop)
        logger.info("Entering main service loop - press Ctrl+C to stop")
        while True:
            try:
                # Check if any scheduled tasks are due and run them
                schedule.run_pending()
                # Sleep for 60 seconds before checking again
                # This prevents excessive CPU usage while maintaining responsiveness
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Service interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                # Continue running even if there are temporary errors
                time.sleep(60)

if __name__ == "__main__":
    """
    Entry point for the data ingestion service.
    
    This script can be run directly for testing or deployed as a container.
    It creates and starts a DataIngestService instance that will:
    - Connect to CSC Allas using credentials from environment variables
    - Download and process data files on a scheduled basis
    - Coordinate with other pipeline services via Redis
    - Store processed files for downstream consumption
    """
    try:
        service = DataIngestService()
        service.start()
    except Exception as e:
        logger.error(f"Failed to start data ingestion service: {str(e)}")
        exit(1)
