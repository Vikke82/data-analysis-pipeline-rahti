import pandas as pd
import numpy as np
import os
import glob
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DataLoader:
    """Handle loading data from the shared data directory."""
    
    def __init__(self):
        self.shared_data_path = "/shared/data"
        
    @property
    def data_path(self):
        """Get the data path, creating it if it doesn't exist."""
        Path(self.shared_data_path).mkdir(parents=True, exist_ok=True)
        return self.shared_data_path
        
    def get_available_files(self):
        """Get list of available cleaned data files."""
        try:
            pattern = os.path.join(self.data_path, "cleaned_*.csv")
            files = glob.glob(pattern)
            
            # Extract just the filenames and sort by modification time
            file_info = []
            for file_path in files:
                filename = os.path.basename(file_path)
                mod_time = os.path.getmtime(file_path)
                file_info.append((filename, mod_time))
                
            # Sort by modification time (newest first)
            file_info.sort(key=lambda x: x[1], reverse=True)
            
            return [info[0] for info in file_info]
            
        except Exception as e:
            logger.error(f"Error getting available files: {str(e)}")
            return []
    
    def load_cleaned_data(self, filename):
        """Load a cleaned data file."""
        try:
            file_path = os.path.join(self.data_path, filename)
            
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
                
            df = pd.read_csv(file_path)
            
            # Convert datetime columns
            datetime_columns = ['ingested_at', 'cleaned_at']
            for col in datetime_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                    
            logger.info(f"Loaded {len(df)} rows from {filename}")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {str(e)}")
            return None
    
    def load_quality_report(self, cleaned_filename):
        """Load the quality report for a cleaned data file."""
        try:
            # Convert cleaned filename to summary filename
            summary_filename = cleaned_filename.replace('cleaned_', 'summary_').replace('.csv', '.json')
            summary_path = os.path.join(self.data_path, summary_filename)
            
            if not os.path.exists(summary_path):
                logger.warning(f"Quality report not found: {summary_path}")
                return None
                
            with open(summary_path, 'r') as f:
                quality_report = json.load(f)
                
            logger.info(f"Loaded quality report for {cleaned_filename}")
            return quality_report
            
        except Exception as e:
            logger.error(f"Error loading quality report for {cleaned_filename}: {str(e)}")
            return None
    
    def get_file_info(self, filename):
        """Get information about a data file."""
        try:
            file_path = os.path.join(self.data_path, filename)
            
            if not os.path.exists(file_path):
                return None
                
            stat = os.stat(file_path)
            
            return {
                'filename': filename,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': pd.Timestamp.fromtimestamp(stat.st_mtime),
                'created': pd.Timestamp.fromtimestamp(stat.st_ctime)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {filename}: {str(e)}")
            return None
    
    def get_data_summary(self):
        """Get summary of all available data."""
        try:
            files = self.get_available_files()
            
            if not files:
                return {
                    'total_files': 0,
                    'total_rows': 0,
                    'total_size_mb': 0,
                    'latest_file': None,
                    'oldest_file': None
                }
            
            total_rows = 0
            total_size = 0
            file_times = []
            
            for filename in files:
                # Get file info
                file_info = self.get_file_info(filename)
                if file_info:
                    total_size += file_info['size_bytes']
                    file_times.append((filename, file_info['modified']))
                
                # Get row count
                try:
                    df = self.load_cleaned_data(filename)
                    if df is not None:
                        total_rows += len(df)
                except:
                    pass
            
            file_times.sort(key=lambda x: x[1])
            
            return {
                'total_files': len(files),
                'total_rows': total_rows,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'latest_file': file_times[-1][0] if file_times else None,
                'oldest_file': file_times[0][0] if file_times else None,
                'latest_update': file_times[-1][1] if file_times else None
            }
            
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return {
                'total_files': 0,
                'total_rows': 0,
                'total_size_mb': 0,
                'latest_file': None,
                'oldest_file': None
            }
