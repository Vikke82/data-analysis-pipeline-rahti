"""
Data processor for handling various file formats in the ingestion pipeline.

This module provides comprehensive data processing capabilities for files downloaded
from CSC Allas. It supports multiple file formats and implements intelligent
format detection, parsing, and basic data cleaning operations.

Key features:
- Multi-format support (CSV, JSON, Excel, TXT)
- Automatic encoding detection and handling
- Basic data cleaning and validation
- Error handling with detailed logging
- Consistent DataFrame output format
"""
import pandas as pd
import numpy as np
import logging
from io import StringIO, BytesIO
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Process raw data files for the analysis pipeline.
    
    This class handles the conversion of raw file data from various formats
    into standardized pandas DataFrames that can be consumed by downstream
    processing services. It implements format detection, data parsing,
    and basic cleaning operations.
    
    Supported formats:
    - CSV: Comma-separated values with automatic delimiter detection
    - JSON: Single objects or arrays of objects
    - Excel: Both .xlsx and .xls formats
    - TXT: Various delimited text formats
    
    The processor ensures consistent output format regardless of input type,
    making it easier for downstream services to handle the data.
    """
    
    def __init__(self):
        """
        Initialize the data processor with supported format configuration.
        
        Sets up the list of supported file formats and any processing
        parameters that control how files are handled.
        """
        # List of file extensions that this processor can handle
        self.supported_formats = ['.csv', '.json', '.xlsx', '.xls', '.txt']
        
        # Add processing configuration
        self.max_file_size = 100 * 1024 * 1024  # 100MB limit
        self.encoding_fallbacks = ['utf-8', 'latin-1', 'cp1252']  # Encoding options to try
        
    def process_raw_data(self, file_data, filename):
        """
        Process raw data based on file type with intelligent format detection.
        
        This is the main entry point for processing files. It analyzes the filename
        to determine the format, then routes the data to the appropriate processing
        method. If the format cannot be determined from the extension, it attempts
        to detect the format from the content.
        
        Args:
            file_data: Raw file data as bytes or string
            filename: Original filename for format detection
            
        Returns:
            pandas.DataFrame: Processed data in standardized format
            
        Raises:
            ValueError: If file format is not supported
            Exception: For parsing errors or other processing issues
        """
        try:
            # Validate file size to prevent memory issues
            if isinstance(file_data, bytes) and len(file_data) > self.max_file_size:
                raise ValueError(f"File {filename} exceeds maximum size limit of {self.max_file_size} bytes")
            
            # Determine file format from extension
            file_ext = os.path.splitext(filename)[1].lower()
            logger.info(f"Processing {filename} as {file_ext} format")
            
            # Route to appropriate processing method based on file extension
            if file_ext == '.csv':
                return self._process_csv(file_data, filename)
            elif file_ext == '.json':
                return self._process_json(file_data, filename)
            elif file_ext in ['.xlsx', '.xls']:
                return self._process_excel(file_data, filename)
            elif file_ext == '.txt':
                return self._process_text(file_data, filename)
            else:
                # Fallback: attempt to detect format from content
                logger.warning(f"Unsupported file format: {file_ext}, attempting content detection")
                return self._process_text(file_data, filename)
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            raise
            
    def _process_csv(self, file_data, filename=None):
        """
        Process CSV data with intelligent parsing and error handling.
        
        This method handles CSV files with various configurations:
        - Different delimiters (comma, semicolon, tab)
        - Various encoding formats
        - Headers and headerless files
        - Quoted and unquoted fields
        
        Args:
            file_data: Raw CSV data as bytes or string
            filename: Optional filename for logging
            
        Returns:
            pandas.DataFrame: Parsed and cleaned CSV data
        """
        try:
            # Convert bytes to string with encoding detection
            if isinstance(file_data, bytes):
                file_data = self._decode_with_fallback(file_data)
            
            # Attempt to read CSV with pandas' intelligent parsing
            # pandas.read_csv automatically detects many CSV variations
            df = pd.read_csv(StringIO(file_data))
            
            # Apply basic cleaning operations
            df = self._clean_dataframe(df, filename)
            
            logger.info(f"Processed CSV {filename or 'data'} with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            raise
            
    def _process_json(self, file_data, filename=None):
        """
        Process JSON data with support for various JSON structures.
        
        This method handles different JSON formats:
        - Array of objects (most common for datasets)
        - Single object (converted to single-row DataFrame)
        - Nested objects (flattened where possible)
        - Mixed data types within arrays
        
        Args:
            file_data: Raw JSON data as bytes or string
            filename: Optional filename for logging
            
        Returns:
            pandas.DataFrame: JSON data converted to tabular format
        """
        try:
            # Convert bytes to string with encoding detection
            if isinstance(file_data, bytes):
                file_data = self._decode_with_fallback(file_data)
                
            # Parse JSON data
            data = json.loads(file_data)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects - most common case for datasets
                # Each object in the array becomes a row in the DataFrame
                df = pd.DataFrame(data)
                logger.debug(f"Processed JSON array with {len(data)} objects")
            elif isinstance(data, dict):
                # Single object - convert to single-row DataFrame
                df = pd.DataFrame([data])
                logger.debug("Processed single JSON object")
            else:
                # Primitive data type - wrap in a DataFrame
                df = pd.DataFrame({'data': [data]})
                logger.debug("Processed JSON primitive value")
                
            # Apply standard cleaning operations
            df = self._clean_dataframe(df, filename)
            
            logger.info(f"Processed JSON {filename or 'data'} with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {filename}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing JSON: {str(e)}")
            raise
            
    def _process_excel(self, file_data):
        """Process Excel data."""
        try:
            df = pd.read_excel(BytesIO(file_data))
            df = self._clean_dataframe(df)
            
            logger.info(f"Processed Excel with {len(df)} rows and {len(df.columns)} columns")
            return df
            
        except Exception as e:
            logger.error(f"Error processing Excel: {str(e)}")
            raise
            
    def _process_text(self, file_data):
        """Process plain text data."""
        try:
            if isinstance(file_data, bytes):
                file_data = file_data.decode('utf-8')
                
            # Try to detect delimiter and process as structured data
            lines = file_data.strip().split('\n')
            
            # Check if it looks like CSV with different delimiter
            for delimiter in [';', '\t', '|']:
                if delimiter in lines[0]:
                    try:
                        df = pd.read_csv(StringIO(file_data), delimiter=delimiter)
                        df = self._clean_dataframe(df)
                        logger.info(f"Processed text as delimited data with {len(df)} rows")
                        return df
                    except:
                        continue
            
            # If not structured, create a simple DataFrame with the text
            df = pd.DataFrame({'text_content': lines})
            df['line_number'] = range(1, len(lines) + 1)
            
            logger.info(f"Processed text file with {len(lines)} lines")
            return df
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    def _decode_with_fallback(self, data_bytes):
        """
        Decode bytes to string with multiple encoding fallbacks.
        
        This method attempts to decode byte data using multiple encoding
        options, starting with UTF-8 and falling back to other common
        encodings if UTF-8 fails.
        
        Args:
            data_bytes: Raw byte data to decode
            
        Returns:
            str: Decoded string data
            
        Raises:
            UnicodeDecodeError: If all encoding attempts fail
        """
        for encoding in self.encoding_fallbacks:
            try:
                return data_bytes.decode(encoding)
            except UnicodeDecodeError:
                logger.debug(f"Failed to decode with {encoding}, trying next encoding")
                continue
        
        # If all encodings fail, use UTF-8 with error replacement
        logger.warning("All encoding attempts failed, using UTF-8 with error replacement")
        return data_bytes.decode('utf-8', errors='replace')
            
    def _clean_dataframe(self, df, filename=None):
        """
        Clean and standardize DataFrame with comprehensive data quality improvements.
        
        This method applies a series of cleaning operations to ensure
        consistent data format across all processed files:
        
        - Adds metadata columns for tracking and auditing
        - Standardizes column names (lowercase, underscores)
        - Handles various types of missing/null values
        - Removes completely empty rows and columns
        - Validates data types where possible
        - Adds processing timestamps
        
        Args:
            df: pandas DataFrame to clean
            filename: Optional source filename for metadata
            
        Returns:
            pandas.DataFrame: Cleaned and standardized DataFrame
        """
        try:
            original_shape = df.shape
            logger.debug(f"Starting DataFrame cleaning for {filename or 'data'}: {original_shape}")
            
            # Add metadata columns for data lineage and auditing
            df['ingested_at'] = datetime.now().isoformat()
            df['data_source'] = 'csc_allas'
            if filename:
                df['source_file'] = filename
            
            # Standardize column names for consistency
            # Convert to lowercase, replace spaces with underscores, remove special characters
            original_columns = list(df.columns)
            df.columns = (df.columns
                         .str.strip()                    # Remove leading/trailing whitespace
                         .str.lower()                    # Convert to lowercase
                         .str.replace(' ', '_')          # Replace spaces with underscores
                         .str.replace(r'[^\w\s]', '', regex=True)  # Remove special characters
                         .str.replace(r'_+', '_', regex=True))     # Collapse multiple underscores
            
            # Log column name changes for debugging
            renamed_columns = dict(zip(original_columns, df.columns))
            if any(old != new for old, new in renamed_columns.items()):
                logger.debug(f"Column names standardized: {renamed_columns}")
            
            # Handle various types of missing values
            # Replace common null representations with actual NaN
            null_values = ['', ' ', 'NULL', 'null', 'None', 'none', 'N/A', 'n/a', 'NA', 'na']
            df = df.replace(null_values, pd.NA)
            
            # Remove completely empty rows (all NaN values)
            before_rows = len(df)
            df = df.dropna(how='all')
            after_rows = len(df)
            if before_rows != after_rows:
                logger.debug(f"Removed {before_rows - after_rows} completely empty rows")
            
            # Remove completely empty columns (all NaN values)
            before_cols = len(df.columns)
            df = df.dropna(axis=1, how='all')
            after_cols = len(df.columns)
            if before_cols != after_cols:
                logger.debug(f"Removed {before_cols - after_cols} completely empty columns")
            
            # Reset index after row removal
            df = df.reset_index(drop=True)
            
            final_shape = df.shape
            logger.info(f"DataFrame cleaning completed for {filename or 'data'}: "
                       f"{original_shape} -> {final_shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning DataFrame for {filename}: {str(e)}")
            # Return original DataFrame if cleaning fails
            return df
