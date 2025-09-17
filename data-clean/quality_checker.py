import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class QualityChecker:
    """Data quality assessment and reporting."""
    
    def __init__(self):
        self.quality_thresholds = {
            'completeness': 80,  # Minimum percentage of non-null values
            'uniqueness': 95,    # Maximum percentage of duplicate rows
            'consistency': 90,   # Minimum percentage of consistent formats
            'validity': 85       # Minimum percentage of valid values
        }
        
    def assess_data_quality(self, df):
        """Perform comprehensive data quality assessment."""
        try:
            logger.info("Starting data quality assessment")
            
            report = {
                'assessment_timestamp': datetime.now().isoformat(),
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'completeness': self._assess_completeness(df),
                'uniqueness': self._assess_uniqueness(df),
                'consistency': self._assess_consistency(df),
                'validity': self._assess_validity(df),
                'column_profiles': self._profile_columns(df),
                'overall_score': 0,
                'recommendations': []
            }
            
            # Calculate overall quality score
            report['overall_score'] = self._calculate_overall_score(report)
            
            # Generate recommendations
            report['recommendations'] = self._generate_recommendations(report)
            
            logger.info(f"Data quality assessment completed. Overall score: {report['overall_score']:.1f}%")
            return report
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {str(e)}")
            raise
            
    def _assess_completeness(self, df):
        """Assess data completeness."""
        metadata_cols = ['ingested_at', 'data_source']
        data_cols = [col for col in df.columns if col not in metadata_cols]
        
        if not data_cols:
            return {'score': 100, 'details': 'No data columns to assess'}
            
        completeness_scores = {}
        total_cells = len(df) * len(data_cols)
        non_null_cells = 0
        
        for col in data_cols:
            non_null = df[col].notna().sum()
            completeness = (non_null / len(df)) * 100 if len(df) > 0 else 0
            completeness_scores[col] = {
                'non_null_count': int(non_null),
                'total_count': len(df),
                'completeness_percentage': round(completeness, 2)
            }
            non_null_cells += non_null
            
        overall_completeness = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
        
        return {
            'score': round(overall_completeness, 2),
            'by_column': completeness_scores,
            'threshold_met': overall_completeness >= self.quality_thresholds['completeness']
        }
        
    def _assess_uniqueness(self, df):
        """Assess data uniqueness."""
        metadata_cols = ['ingested_at', 'data_source']
        data_cols = [col for col in df.columns if col not in metadata_cols]
        
        if not data_cols:
            return {'score': 100, 'details': 'No data columns to assess'}
            
        # Check for duplicate rows
        duplicates = df.duplicated(subset=data_cols) if data_cols else df.duplicated()
        duplicate_count = duplicates.sum()
        uniqueness_percentage = ((len(df) - duplicate_count) / len(df)) * 100 if len(df) > 0 else 100
        
        # Check uniqueness by column
        column_uniqueness = {}
        for col in data_cols:
            unique_values = df[col].nunique()
            total_values = df[col].notna().sum()
            col_uniqueness = (unique_values / total_values) * 100 if total_values > 0 else 0
            column_uniqueness[col] = {
                'unique_values': int(unique_values),
                'total_values': int(total_values),
                'uniqueness_percentage': round(col_uniqueness, 2)
            }
            
        return {
            'score': round(uniqueness_percentage, 2),
            'duplicate_rows': int(duplicate_count),
            'by_column': column_uniqueness,
            'threshold_met': uniqueness_percentage >= self.quality_thresholds['uniqueness']
        }
        
    def _assess_consistency(self, df):
        """Assess data consistency."""
        consistency_scores = {}
        total_score = 0
        columns_assessed = 0
        
        for col in df.columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            columns_assessed += 1
            
            if df[col].dtype == 'object':
                # Check text consistency
                consistency_scores[col] = self._check_text_consistency(df[col])
            elif df[col].dtype in ['int64', 'float64']:
                # Check numeric consistency
                consistency_scores[col] = self._check_numeric_consistency(df[col])
            elif 'datetime' in str(df[col].dtype):
                # Check datetime consistency
                consistency_scores[col] = self._check_datetime_consistency(df[col])
            else:
                consistency_scores[col] = {'score': 100, 'issues': []}
                
            total_score += consistency_scores[col]['score']
            
        overall_consistency = total_score / columns_assessed if columns_assessed > 0 else 100
        
        return {
            'score': round(overall_consistency, 2),
            'by_column': consistency_scores,
            'threshold_met': overall_consistency >= self.quality_thresholds['consistency']
        }
        
    def _check_text_consistency(self, series):
        """Check consistency in text data."""
        issues = []
        score = 100
        
        # Check for mixed case
        if series.notna().any():
            text_values = series.dropna().astype(str)
            
            # Check case consistency
            lower_count = text_values.str.islower().sum()
            upper_count = text_values.str.isupper().sum()
            mixed_count = len(text_values) - lower_count - upper_count
            
            if mixed_count > len(text_values) * 0.3:
                issues.append("Inconsistent text casing")
                score -= 20
                
            # Check for leading/trailing whitespace
            whitespace_count = (text_values != text_values.str.strip()).sum()
            if whitespace_count > 0:
                issues.append(f"{whitespace_count} values with leading/trailing whitespace")
                score -= 10
                
            # Check for empty strings
            empty_count = (text_values == '').sum()
            if empty_count > 0:
                issues.append(f"{empty_count} empty strings")
                score -= 15
                
        return {'score': max(0, score), 'issues': issues}
        
    def _check_numeric_consistency(self, series):
        """Check consistency in numeric data."""
        issues = []
        score = 100
        
        if series.notna().any():
            # Check for extreme outliers
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            
            extreme_lower = Q1 - 3 * IQR
            extreme_upper = Q3 + 3 * IQR
            
            extreme_outliers = ((series < extreme_lower) | (series > extreme_upper)).sum()
            if extreme_outliers > len(series) * 0.05:
                issues.append(f"{extreme_outliers} extreme outliers detected")
                score -= 25
                
        return {'score': max(0, score), 'issues': issues}
        
    def _check_datetime_consistency(self, series):
        """Check consistency in datetime data."""
        issues = []
        score = 100
        
        if series.notna().any():
            # Check for future dates (potential data entry errors)
            future_dates = (series > pd.Timestamp.now()).sum()
            if future_dates > 0:
                issues.append(f"{future_dates} future dates detected")
                score -= 20
                
            # Check for very old dates (potential errors)
            very_old_dates = (series < pd.Timestamp('1900-01-01')).sum()
            if very_old_dates > 0:
                issues.append(f"{very_old_dates} dates before 1900")
                score -= 15
                
        return {'score': max(0, score), 'issues': issues}
        
    def _assess_validity(self, df):
        """Assess data validity."""
        validity_scores = {}
        total_score = 0
        columns_assessed = 0
        
        for col in df.columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            columns_assessed += 1
            valid_count = df[col].notna().sum()
            total_count = len(df)
            validity_percentage = (valid_count / total_count) * 100 if total_count > 0 else 100
            
            validity_scores[col] = {
                'valid_count': int(valid_count),
                'total_count': int(total_count),
                'validity_percentage': round(validity_percentage, 2)
            }
            
            total_score += validity_percentage
            
        overall_validity = total_score / columns_assessed if columns_assessed > 0 else 100
        
        return {
            'score': round(overall_validity, 2),
            'by_column': validity_scores,
            'threshold_met': overall_validity >= self.quality_thresholds['validity']
        }
        
    def _profile_columns(self, df):
        """Create detailed profiles for each column."""
        profiles = {}
        
        for col in df.columns:
            if col in ['ingested_at', 'data_source']:
                continue
                
            profile = {
                'data_type': str(df[col].dtype),
                'non_null_count': int(df[col].notna().sum()),
                'null_count': int(df[col].isna().sum()),
                'unique_count': int(df[col].nunique()),
            }
            
            if df[col].dtype in ['int64', 'float64']:
                profile.update({
                    'min_value': float(df[col].min()) if df[col].notna().any() else None,
                    'max_value': float(df[col].max()) if df[col].notna().any() else None,
                    'mean_value': float(df[col].mean()) if df[col].notna().any() else None,
                    'std_deviation': float(df[col].std()) if df[col].notna().any() else None
                })
            elif df[col].dtype == 'object':
                profile.update({
                    'avg_length': float(df[col].astype(str).str.len().mean()) if df[col].notna().any() else None,
                    'min_length': int(df[col].astype(str).str.len().min()) if df[col].notna().any() else None,
                    'max_length': int(df[col].astype(str).str.len().max()) if df[col].notna().any() else None
                })
                
            profiles[col] = profile
            
        return profiles
        
    def _calculate_overall_score(self, report):
        """Calculate overall quality score."""
        scores = [
            report['completeness']['score'],
            report['uniqueness']['score'],
            report['consistency']['score'],
            report['validity']['score']
        ]
        return sum(scores) / len(scores)
        
    def _generate_recommendations(self, report):
        """Generate quality improvement recommendations."""
        recommendations = []
        
        # Completeness recommendations
        if not report['completeness']['threshold_met']:
            recommendations.append(
                f"Improve data completeness (current: {report['completeness']['score']:.1f}%, "
                f"target: {self.quality_thresholds['completeness']}%)"
            )
            
        # Uniqueness recommendations
        if not report['uniqueness']['threshold_met']:
            recommendations.append(
                f"Address duplicate records (current uniqueness: {report['uniqueness']['score']:.1f}%, "
                f"target: {self.quality_thresholds['uniqueness']}%)"
            )
            
        # Consistency recommendations
        if not report['consistency']['threshold_met']:
            recommendations.append(
                f"Improve data consistency (current: {report['consistency']['score']:.1f}%, "
                f"target: {self.quality_thresholds['consistency']}%)"
            )
            
        # Validity recommendations
        if not report['validity']['threshold_met']:
            recommendations.append(
                f"Improve data validity (current: {report['validity']['score']:.1f}%, "
                f"target: {self.quality_thresholds['validity']}%)"
            )
            
        if not recommendations:
            recommendations.append("Data quality meets all thresholds")
            
        return recommendations
