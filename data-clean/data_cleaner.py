import pandas as pd
import numpy as np
import logging
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
import re

logger = logging.getLogger(__name__)

class DataCleaner:
    """Advanced data cleaning and preprocessing."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def clean_data(self, df):
        """Main data cleaning pipeline."""
        try:
            logger.info("Starting data cleaning process")
            
            # Make a copy to avoid modifying original
            cleaned_df = df.copy()
            
            # Remove duplicate rows
            cleaned_df = self._remove_duplicates(cleaned_df)
            
            # Clean column names
            cleaned_df = self._clean_column_names(cleaned_df)
            
            # Handle missing values
            cleaned_df = self._handle_missing_values(cleaned_df)
            
            # Clean text fields
            cleaned_df = self._clean_text_fields(cleaned_df)
            
            # Standardize data types
            cleaned_df = self._standardize_data_types(cleaned_df)
            
            # Remove outliers
            cleaned_df = self._handle_outliers(cleaned_df)
            
            # Add data quality indicators
            cleaned_df = self._add_quality_indicators(cleaned_df, df)
            
            logger.info(f"Data cleaning completed: {len(cleaned_df)} rows retained")
            return cleaned_df
            
        except Exception as e:
            logger.error(f"Error in data cleaning: {str(e)}")
            raise
            
    def _remove_duplicates(self, df):
        """Remove duplicate rows."""
        initial_count = len(df)
        
        # Keep metadata columns separate for duplicate detection
        metadata_cols = ['ingested_at', 'data_source']
        data_cols = [col for col in df.columns if col not in metadata_cols]
        
        # Remove duplicates based on data columns only
        if data_cols:
            df_deduplicated = df.drop_duplicates(subset=data_cols, keep='first')
        else:
            df_deduplicated = df.drop_duplicates(keep='first')
            
        removed_count = initial_count - len(df_deduplicated)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate rows")
            
        return df_deduplicated
        
    def _clean_column_names(self, df):
        """Standardize column names."""
        new_columns = {}
        
        for col in df.columns:
            # Keep metadata columns unchanged
            if col in ['ingested_at', 'data_source']:
                new_columns[col] = col
                continue
                
            # Clean other column names
            clean_name = (
                col.lower()
                .strip()
                .replace(' ', '_')
                .replace('-', '_')
                .replace('.', '_')
                .replace('__', '_')
            )
            
            # Remove special characters except underscore
            clean_name = re.sub(r'[^\w_]', '', clean_name)
            
            # Ensure doesn't start with number
            if clean_name and clean_name[0].isdigit():
                clean_name = f'col_{clean_name}'
                
            new_columns[col] = clean_name or f'col_{df.columns.get_loc(col)}'
            
        return df.rename(columns=new_columns)
        
    def _handle_missing_values(self, df):
        """Handle missing values based on column type."""
        for col in df.columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            # Check missing value percentage
            missing_pct = df[col].isna().sum() / len(df) * 100
            
            if missing_pct > 90:
                # Drop columns with > 90% missing values
                df = df.drop(columns=[col])
                logger.info(f"Dropped column '{col}' (>{missing_pct:.1f}% missing)")
                continue
                
            if missing_pct > 0:
                if df[col].dtype in ['object', 'string']:
                    # Fill text columns with 'unknown'
                    df[col] = df[col].fillna('unknown')
                elif df[col].dtype in ['int64', 'float64']:
                    # Fill numeric columns with median
                    df[col] = df[col].fillna(df[col].median())
                else:
                    # Fill other types with mode or forward fill
                    mode_val = df[col].mode()
                    if not mode_val.empty:
                        df[col] = df[col].fillna(mode_val[0])
                    else:
                        df[col] = df[col].fillna(method='ffill')
                        
                logger.info(f"Filled {missing_pct:.1f}% missing values in '{col}'")
                
        return df
        
    def _clean_text_fields(self, df):
        """Clean text fields."""
        text_columns = df.select_dtypes(include=['object', 'string']).columns
        
        for col in text_columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            # Strip whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Replace empty strings with 'unknown'
            df[col] = df[col].replace('', 'unknown')
            df[col] = df[col].replace('nan', 'unknown')
            
            # Convert to lowercase for consistency
            df[col] = df[col].str.lower()
            
        return df
        
    def _standardize_data_types(self, df):
        """Standardize and optimize data types."""
        for col in df.columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            # Try to convert to numeric if possible
            if df[col].dtype == 'object':
                # Try to convert to datetime first
                try:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                    if df[col].dtype == 'datetime64[ns]':
                        logger.info(f"Converted '{col}' to datetime")
                        continue
                except:
                    pass
                    
                # Try to convert to numeric
                try:
                    numeric_col = pd.to_numeric(df[col], errors='coerce')
                    if not numeric_col.isna().all():
                        # If conversion was mostly successful, keep it
                        if numeric_col.notna().sum() / len(df) > 0.5:
                            df[col] = numeric_col
                            logger.info(f"Converted '{col}' to numeric")
                except:
                    pass
                    
        return df
        
    def _handle_outliers(self, df):
        """Handle outliers in numeric columns."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Count outliers
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            if len(outliers) > 0:
                outlier_pct = len(outliers) / len(df) * 100
                
                if outlier_pct < 5:  # Remove if less than 5% of data
                    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
                    logger.info(f"Removed {len(outliers)} outliers from '{col}' ({outlier_pct:.1f}%)")
                else:
                    # Cap outliers instead of removing
                    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                    logger.info(f"Capped {len(outliers)} outliers in '{col}' ({outlier_pct:.1f}%)")
                    
        return df
        
    def _add_quality_indicators(self, cleaned_df, original_df):
        """Add data quality indicators."""
        # Add processing timestamp
        cleaned_df['cleaned_at'] = datetime.now().isoformat()
        
        # Add data completeness score for each row
        metadata_cols = ['ingested_at', 'data_source', 'cleaned_at']
        data_cols = [col for col in cleaned_df.columns if col not in metadata_cols]
        
        if data_cols:
            # Calculate completeness score (percentage of non-null values)
            cleaned_df['completeness_score'] = (
                cleaned_df[data_cols].notna().sum(axis=1) / len(data_cols) * 100
            ).round(2)
            
        return cleaned_df
