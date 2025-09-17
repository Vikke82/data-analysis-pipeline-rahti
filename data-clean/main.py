"""
Data cleaning service for the CSC Allas data analysis pipeline.

This service acts as the second stage of the data pipeline, responsible for:
- Monitoring for raw data files from the ingestion service
- Applying comprehensive data cleaning and validation operations
- Performing quality assessments and generating reports
- Preparing clean data for visualization and analysis
- Coordinating with other services via Redis

The service implements advanced data quality techniques including:
- Duplicate detection and removal
- Missing value imputation
- Outlier detection and handling
- Data type standardization
- Column name normalization
- Statistical quality scoring
"""
import os
import time
import logging
import schedule
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from data_cleaner import DataCleaner
from quality_checker import QualityChecker
import redis
import json
import glob

# Configure logging with detailed formatting for monitoring and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleanService:
    """
    Main data cleaning service for processing ingested data.
    
    This service monitors the shared data directory for raw files created by
    the data ingestion service and applies comprehensive cleaning operations.
    It coordinates with other pipeline services through Redis and maintains
    detailed quality metrics for monitoring and reporting.
    
    Key responsibilities:
    - File monitoring and processing coordination
    - Data cleaning and validation
    - Quality assessment and scoring
    - Error handling and recovery
    - Status reporting via Redis
    
    The service runs continuously on a scheduled basis, processing new files
    as they become available and maintaining pipeline health information.
    """
    
    def __init__(self):
        """
        Initialize the data cleaning service with all required components.
        
        Sets up connections to data processing components, Redis coordination,
        and configures file system paths for data exchange.
        """
        # Initialize data processing components
        self.data_cleaner = DataCleaner()
        self.quality_checker = QualityChecker()
        
        # Redis client for inter-service coordination and status tracking
        # Use environment variables for Redis connection or fallback to defaults
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # File system configuration for data pipeline
        # Use environment variable or fallback to writable directory
        self.shared_data_path = os.getenv('SHARED_DATA_PATH', '/tmp/shared/data')
        
        # Ensure the shared data directory exists and is writable
        os.makedirs(self.shared_data_path, exist_ok=True)
        
        self.raw_data_pattern = "raw_*.csv"          # Pattern for ingested files
        self.cleaned_data_prefix = "cleaned_"        # Prefix for processed files
        self.summary_prefix = "summary_"             # Prefix for quality reports
        
        # Processing configuration
        self.max_file_age_hours = 24  # Skip files older than 24 hours
        
    def run_cleaning_cycle(self):
        """
        Execute a complete data cleaning cycle.
        
        This is the main orchestration method that:
        1. Scans for new raw data files from the ingestion service
        2. Processes each file through the cleaning pipeline
        3. Generates quality assessment reports
        4. Updates Redis with processing status
        5. Saves cleaned data for visualization service
        
        Error handling ensures that issues with individual files don't
        disrupt the entire cleaning process.
        """
        try:
            logger.info("Starting data cleaning cycle - scanning for raw files")
            
            # Find raw data files that need processing
            raw_files = self._find_raw_files()
            if not raw_files:
                logger.info("No raw files to process - waiting for ingestion service")
                return
                
            logger.info(f"Found {len(raw_files)} raw files to process")
            
            # Process each raw file through the cleaning pipeline
            for raw_file in raw_files:
                try:
                    self._process_file(raw_file)
                except Exception as e:
                    # Individual file errors shouldn't stop the entire process
                    logger.error(f"Error processing {raw_file}: {str(e)}")
                    self._update_file_status(raw_file, 'error')
                    self._update_processing_status(raw_file, 'error', str(e))
                    
            self._update_cleaning_status()
            logger.info("Data cleaning cycle completed")
            
        except Exception as e:
            logger.error(f"Error in cleaning cycle: {str(e)}")
            
    def _find_raw_files(self):
        """Find raw data files that need cleaning."""
        pattern = os.path.join(self.shared_data_path, self.raw_data_pattern)
        raw_files = glob.glob(pattern)
        
        # Filter out files that have already been processed
        unprocessed_files = []
        for raw_file in raw_files:
            filename = os.path.basename(raw_file)
            status_key = f"clean_status:{filename}"
            
            last_status = self.redis_client.get(status_key)
            if last_status != 'completed':
                unprocessed_files.append(raw_file)
                
        return unprocessed_files
        
    def _process_file(self, raw_file_path):
        """Process a single raw data file."""
        filename = os.path.basename(raw_file_path)
        logger.info(f"Processing file: {filename}")
        
        # Update status to processing
        self._update_processing_status(filename, 'processing')
        
        try:
            # Load raw data
            df = pd.read_csv(raw_file_path)
            logger.info(f"Loaded {len(df)} rows from {filename}")
            
            # Run quality checks
            quality_report = self.quality_checker.assess_data_quality(df)
            
            # Clean the data
            cleaned_df = self.data_cleaner.clean_data(df)
            logger.info(f"Cleaned data: {len(cleaned_df)} rows remaining")
            
            # Generate cleaning summary
            cleaning_summary = self._generate_cleaning_summary(df, cleaned_df, quality_report)
            
            # Save cleaned data
            cleaned_filename = filename.replace('raw_', self.cleaned_data_prefix)
            cleaned_path = os.path.join(self.shared_data_path, cleaned_filename)
            cleaned_df.to_csv(cleaned_path, index=False)
            
            # Save cleaning summary
            summary_filename = filename.replace('raw_', 'summary_').replace('.csv', '.json')
            summary_path = os.path.join(self.shared_data_path, summary_filename)
            
            with open(summary_path, 'w') as f:
                json.dump(cleaning_summary, f, indent=2, default=str)
                
            # Update status to completed
            self._update_processing_status(filename, 'completed')
            
            logger.info(f"Successfully processed {filename}")
            
        except Exception as e:
            logger.error(f"Failed to process {filename}: {str(e)}")
            self._update_processing_status(filename, 'error', str(e))
            raise
            
    def _generate_cleaning_summary(self, original_df, cleaned_df, quality_report):
        """Generate a summary of the cleaning process."""
        return {
            'original_rows': len(original_df),
            'cleaned_rows': len(cleaned_df),
            'rows_removed': len(original_df) - len(cleaned_df),
            'removal_percentage': ((len(original_df) - len(cleaned_df)) / len(original_df)) * 100,
            'original_columns': len(original_df.columns),
            'cleaned_columns': len(cleaned_df.columns),
            'quality_report': quality_report,
            'cleaning_timestamp': datetime.now().isoformat(),
            'data_types': {col: str(dtype) for col, dtype in cleaned_df.dtypes.items()},
            'column_stats': {
                col: {
                    'non_null_count': int(cleaned_df[col].notna().sum()),
                    'null_count': int(cleaned_df[col].isna().sum()),
                    'unique_values': int(cleaned_df[col].nunique())
                }
                for col in cleaned_df.columns
                if col not in ['ingested_at', 'data_source']
            }
        }
        
    def _update_processing_status(self, filename, status, error_message=None):
        """Update file processing status in Redis."""
        status_key = f"clean_status:{filename}"
        status_data = {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'error_message': error_message
        }
        self.redis_client.set(status_key, json.dumps(status_data))
        
    def _update_cleaning_status(self):
        """Update overall cleaning status in Redis."""
        cleaning_info = {
            'last_cleaning': datetime.now().isoformat(),
            'status': 'completed'
        }
        self.redis_client.set('cleaning_status', json.dumps(cleaning_info))
        
    def start(self):
        """Start the data cleaning service."""
        logger.info("Starting Data Clean Service")
        
        # Initial run
        self.run_cleaning_cycle()
        
        # Schedule regular runs (every 10 minutes)
        schedule.every(10).minutes.do(self.run_cleaning_cycle)
        
        # Keep the service running
        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    service = DataCleanService()
    service.start()
