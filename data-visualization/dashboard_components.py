import streamlit as st
import pandas as pd
import json
import redis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DashboardComponents:
    """Reusable dashboard components."""
    
    def __init__(self):
        self.redis_client = None
        try:
            self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}")
    
    def get_pipeline_status(self):
        """Get the current status of the pipeline."""
        status = {
            'ingestion': {'status': 'unknown', 'last_run': None, 'message': 'No data available'},
            'cleaning': {'status': 'unknown', 'last_run': None, 'message': 'No data available'},
            'overall': 'unknown'
        }
        
        if not self.redis_client:
            return status
        
        try:
            # Check ingestion status
            sync_status = self.redis_client.get('sync_status')
            if sync_status:
                sync_data = json.loads(sync_status)
                status['ingestion'] = {
                    'status': sync_data.get('status', 'unknown'),
                    'last_run': sync_data.get('last_sync'),
                    'message': 'Data ingestion completed'
                }
            
            # Check cleaning status
            cleaning_status = self.redis_client.get('cleaning_status')
            if cleaning_status:
                cleaning_data = json.loads(cleaning_status)
                status['cleaning'] = {
                    'status': cleaning_data.get('status', 'unknown'),
                    'last_run': cleaning_data.get('last_cleaning'),
                    'message': 'Data cleaning completed'
                }
            
            # Determine overall status
            if (status['ingestion']['status'] == 'completed' and 
                status['cleaning']['status'] == 'completed'):
                status['overall'] = 'healthy'
            elif 'error' in [status['ingestion']['status'], status['cleaning']['status']]:
                status['overall'] = 'error'
            else:
                status['overall'] = 'warning'
                
        except Exception as e:
            logger.error(f"Error getting pipeline status: {str(e)}")
            
        return status
    
    def display_pipeline_status(self, status):
        """Display pipeline status indicators."""
        
        # Overall status
        if status['overall'] == 'healthy':
            st.success("🟢 Pipeline Healthy")
        elif status['overall'] == 'error':
            st.error("🔴 Pipeline Error")
        else:
            st.warning("🟡 Pipeline Warning")
        
        # Detailed status
        with st.expander("Detailed Status", expanded=False):
            
            # Ingestion status
            st.write("**Data Ingestion:**")
            ingestion = status['ingestion']
            if ingestion['status'] == 'completed':
                st.success(f"✅ {ingestion['message']}")
            elif ingestion['status'] == 'error':
                st.error(f"❌ Error in ingestion")
            else:
                st.info(f"ℹ️ {ingestion['message']}")
            
            if ingestion['last_run']:
                st.caption(f"Last run: {ingestion['last_run']}")
            
            # Cleaning status
            st.write("**Data Cleaning:**")
            cleaning = status['cleaning']
            if cleaning['status'] == 'completed':
                st.success(f"✅ {cleaning['message']}")
            elif cleaning['status'] == 'error':
                st.error(f"❌ Error in cleaning")
            else:
                st.info(f"ℹ️ {cleaning['message']}")
            
            if cleaning['last_run']:
                st.caption(f"Last run: {cleaning['last_run']}")
    
    def display_overview_metrics(self, df, quality_report):
        """Display overview metrics in a grid layout."""
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📊 Total Rows",
                value=f"{len(df):,}",
                help="Total number of data rows"
            )
        
        with col2:
            st.metric(
                label="📋 Columns",
                value=len(df.columns),
                help="Total number of columns"
            )
        
        with col3:
            if quality_report:
                quality_score = quality_report.get('overall_score', 0)
                st.metric(
                    label="🎯 Quality Score",
                    value=f"{quality_score:.1f}%",
                    help="Overall data quality score"
                )
            else:
                st.metric(
                    label="🎯 Quality Score",
                    value="N/A",
                    help="Quality report not available"
                )
        
        with col4:
            # Calculate data freshness
            if 'cleaned_at' in df.columns:
                try:
                    latest_clean = pd.to_datetime(df['cleaned_at']).max()
                    hours_ago = (datetime.now() - latest_clean).total_seconds() / 3600
                    st.metric(
                        label="🕒 Data Age",
                        value=f"{hours_ago:.1f}h",
                        help="Hours since last data update"
                    )
                except:
                    st.metric(label="🕒 Data Age", value="Unknown")
            else:
                st.metric(label="🕒 Data Age", value="Unknown")
    
    def display_quality_metrics(self, quality_report):
        """Display detailed quality metrics."""
        
        if not quality_report:
            st.warning("No quality report available")
            return
        
        # Quality score breakdown
        col1, col2, col3, col4 = st.columns(4)
        
        quality_metrics = [
            ("Completeness", quality_report.get('completeness', {}).get('score', 0)),
            ("Uniqueness", quality_report.get('uniqueness', {}).get('score', 0)),
            ("Consistency", quality_report.get('consistency', {}).get('score', 0)),
            ("Validity", quality_report.get('validity', {}).get('score', 0))
        ]
        
        for i, (metric_name, score) in enumerate(quality_metrics):
            with [col1, col2, col3, col4][i]:
                # Color coding based on score
                if score >= 80:
                    color = "normal"
                elif score >= 60:
                    color = "warning" 
                else:
                    color = "error"
                
                st.metric(
                    label=f"🎯 {metric_name}",
                    value=f"{score:.1f}%"
                )
        
        # Quality recommendations
        recommendations = quality_report.get('recommendations', [])
        if recommendations:
            with st.expander("🔍 Quality Recommendations", expanded=False):
                for rec in recommendations:
                    st.write(f"• {rec}")
    
    def apply_time_filter(self, df, time_range):
        """Apply time-based filtering to the dataframe."""
        
        if time_range == "All Time" or 'cleaned_at' not in df.columns:
            return df
        
        try:
            # Convert to datetime if not already
            df['cleaned_at'] = pd.to_datetime(df['cleaned_at'])
            
            # Calculate time threshold
            now = datetime.now()
            if time_range == "Last Hour":
                threshold = now - timedelta(hours=1)
            elif time_range == "Last 6 Hours":
                threshold = now - timedelta(hours=6)
            elif time_range == "Last Day":
                threshold = now - timedelta(days=1)
            elif time_range == "Last Week":
                threshold = now - timedelta(weeks=1)
            else:
                return df
            
            # Filter data
            filtered_df = df[df['cleaned_at'] >= threshold]
            
            if len(filtered_df) == 0:
                st.warning(f"No data found for time range: {time_range}")
                return df
            
            return filtered_df
            
        except Exception as e:
            logger.error(f"Error applying time filter: {str(e)}")
            st.warning(f"Could not apply time filter: {str(e)}")
            return df
    
    def create_data_profiling_card(self, df, column):
        """Create a data profiling card for a specific column."""
        
        with st.container():
            st.subheader(f"Profile: {column}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Basic Info:**")
                st.write(f"Data Type: {df[column].dtype}")
                st.write(f"Total Values: {len(df[column])}")
                st.write(f"Non-null Values: {df[column].notna().sum()}")
                st.write(f"Null Values: {df[column].isna().sum()}")
                
            with col2:
                st.write("**Uniqueness:**")
                st.write(f"Unique Values: {df[column].nunique()}")
                
                if df[column].dtype in ['object', 'string']:
                    st.write(f"Most Common: {df[column].mode().iloc[0] if len(df[column].mode()) > 0 else 'N/A'}")
                elif df[column].dtype in ['int64', 'float64']:
                    st.write(f"Mean: {df[column].mean():.2f}")
                    st.write(f"Std Dev: {df[column].std():.2f}")
    
    def display_processing_timeline(self):
        """Display a timeline of data processing events."""
        
        if not self.redis_client:
            st.info("Processing timeline not available (Redis not connected)")
            return
        
        try:
            # Get all processing events from Redis
            events = []
            
            # Get file processing events
            keys = self.redis_client.keys("clean_status:*")
            for key in keys:
                try:
                    status_data = json.loads(self.redis_client.get(key))
                    filename = key.replace("clean_status:", "")
                    
                    events.append({
                        'timestamp': pd.to_datetime(status_data['timestamp']),
                        'event': f"Cleaned {filename}",
                        'status': status_data['status'],
                        'type': 'cleaning'
                    })
                except:
                    continue
            
            if events:
                # Sort by timestamp
                events.sort(key=lambda x: x['timestamp'], reverse=True)
                
                st.subheader("📅 Processing Timeline")
                
                # Display recent events
                for event in events[:10]:  # Show last 10 events
                    status_color = {
                        'completed': '🟢',
                        'processing': '🟡',
                        'error': '🔴'
                    }.get(event['status'], '⚪')
                    
                    st.write(f"{status_color} {event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {event['event']}")
            else:
                st.info("No processing events found")
                
        except Exception as e:
            logger.error(f"Error displaying processing timeline: {str(e)}")
            st.warning("Could not load processing timeline")
    
    @staticmethod
    def format_number(number):
        """Format numbers for display."""
        if number >= 1_000_000:
            return f"{number/1_000_000:.1f}M"
        elif number >= 1_000:
            return f"{number/1_000:.1f}K"
        else:
            return str(number)
    
    @staticmethod
    def format_bytes(bytes_size):
        """Format byte size for display."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
