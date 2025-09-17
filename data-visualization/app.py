import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import os
import glob
from datetime import datetime, timedelta
from data_loader import DataLoader
from visualizations import DataVisualizer
from dashboard_components import DashboardComponents
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Data Analysis Pipeline Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application function."""
    
    # Initialize components
    data_loader = DataLoader()
    visualizer = DataVisualizer()
    dashboard = DashboardComponents()
    
    # App header
    st.markdown('<h1 class="main-header">📊 Data Analysis Pipeline Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Pipeline Controls")
        
        # Pipeline status
        st.subheader("Pipeline Status")
        pipeline_status = dashboard.get_pipeline_status()
        dashboard.display_pipeline_status(pipeline_status)
        
        # Data refresh
        st.subheader("Data Controls")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        # File selection
        st.subheader("Data Selection")
        available_files = data_loader.get_available_files()
        
        if available_files:
            selected_file = st.selectbox(
                "Select Dataset",
                available_files,
                index=0
            )
        else:
            st.warning("No processed data files found")
            selected_file = None
            
        # Time range filter
        st.subheader("Time Range")
        time_range = st.selectbox(
            "Select Time Range",
            ["Last Hour", "Last 6 Hours", "Last Day", "Last Week", "All Time"],
            index=2
        )
    
    # Main content area
    if selected_file:
        display_dashboard(selected_file, data_loader, visualizer, dashboard, time_range)
    else:
        display_no_data_message()

def display_dashboard(selected_file, data_loader, visualizer, dashboard, time_range):
    """Display the main dashboard content."""
    
    try:
        # Load data
        with st.spinner("Loading data..."):
            df = data_loader.load_cleaned_data(selected_file)
            quality_report = data_loader.load_quality_report(selected_file)
        
        if df is None or df.empty:
            st.error("Failed to load data or dataset is empty")
            return
            
        # Apply time filter
        df_filtered = dashboard.apply_time_filter(df, time_range)
        
        # Overview metrics
        st.header("📈 Data Overview")
        dashboard.display_overview_metrics(df_filtered, quality_report)
        
        # Data quality section
        st.header("🎯 Data Quality Assessment")
        if quality_report:
            dashboard.display_quality_metrics(quality_report)
        else:
            st.warning("Quality report not available for this dataset")
        
        # Data exploration tabs
        st.header("🔍 Data Exploration")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Statistical Summary", 
            "📈 Visualizations", 
            "🔍 Data Explorer", 
            "📋 Raw Data"
        ])
        
        with tab1:
            display_statistical_summary(df_filtered, dashboard)
            
        with tab2:
            display_visualizations(df_filtered, visualizer)
            
        with tab3:
            display_data_explorer(df_filtered, dashboard)
            
        with tab4:
            display_raw_data(df_filtered)
            
    except Exception as e:
        st.error(f"Error displaying dashboard: {str(e)}")
        logger.error(f"Dashboard error: {str(e)}")

def display_statistical_summary(df, dashboard):
    """Display statistical summary of the data."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Numeric Columns Summary")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        numeric_cols = [col for col in numeric_cols if col not in ['completeness_score']]
        
        if len(numeric_cols) > 0:
            numeric_summary = df[numeric_cols].describe()
            st.dataframe(numeric_summary, use_container_width=True)
        else:
            st.info("No numeric columns found")
    
    with col2:
        st.subheader("Categorical Columns Summary")
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns
        categorical_cols = [col for col in categorical_cols 
                          if col not in ['ingested_at', 'data_source', 'cleaned_at']]
        
        if len(categorical_cols) > 0:
            for col in categorical_cols[:5]:  # Show first 5 categorical columns
                st.write(f"**{col}:**")
                value_counts = df[col].value_counts().head(10)
                st.bar_chart(value_counts)
        else:
            st.info("No categorical columns found")

def display_visualizations(df, visualizer):
    """Display various data visualizations."""
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    # Remove metadata columns
    metadata_cols = ['ingested_at', 'data_source', 'cleaned_at', 'completeness_score']
    numeric_cols = [col for col in numeric_cols if col not in metadata_cols]
    categorical_cols = [col for col in categorical_cols if col not in metadata_cols]
    
    if len(numeric_cols) == 0 and len(categorical_cols) == 0:
        st.info("No suitable columns for visualization")
        return
    
    # Correlation heatmap
    if len(numeric_cols) > 1:
        st.subheader("📊 Correlation Heatmap")
        fig_corr = visualizer.create_correlation_heatmap(df[numeric_cols])
        st.plotly_chart(fig_corr, use_container_width=True)
    
    # Distribution plots
    if len(numeric_cols) > 0:
        st.subheader("📈 Distribution Plots")
        selected_numeric = st.selectbox("Select numeric column", numeric_cols)
        
        col1, col2 = st.columns(2)
        with col1:
            fig_hist = visualizer.create_histogram(df, selected_numeric)
            st.plotly_chart(fig_hist, use_container_width=True)
            
        with col2:
            fig_box = visualizer.create_box_plot(df, selected_numeric)
            st.plotly_chart(fig_box, use_container_width=True)
    
    # Scatter plots
    if len(numeric_cols) > 1:
        st.subheader("🎯 Scatter Plot Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            x_col = st.selectbox("Select X axis", numeric_cols, key="scatter_x")
        with col2:
            y_col = st.selectbox("Select Y axis", numeric_cols, key="scatter_y", 
                                index=1 if len(numeric_cols) > 1 else 0)
        
        if x_col != y_col:
            color_col = None
            if len(categorical_cols) > 0:
                color_col = st.selectbox("Color by (optional)", 
                                       ["None"] + categorical_cols, key="scatter_color")
                color_col = None if color_col == "None" else color_col
                
            fig_scatter = visualizer.create_scatter_plot(df, x_col, y_col, color_col)
            st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Time series (if date columns exist)
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if len(date_cols) > 0 and len(numeric_cols) > 0:
        st.subheader("⏰ Time Series Analysis")
        date_col = st.selectbox("Select date column", date_cols)
        value_col = st.selectbox("Select value column", numeric_cols, key="timeseries")
        
        fig_timeseries = visualizer.create_time_series_plot(df, date_col, value_col)
        st.plotly_chart(fig_timeseries, use_container_width=True)

def display_data_explorer(df, dashboard):
    """Display interactive data explorer."""
    
    st.subheader("🔍 Interactive Data Explorer")
    
    # Column information
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Dataset Shape:**", df.shape)
        st.write("**Memory Usage:**", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    with col2:
        st.write("**Data Types:**")
        dtype_counts = df.dtypes.value_counts()
        st.write(dtype_counts)
    
    # Column selector and filters
    st.subheader("Column Analysis")
    selected_column = st.selectbox("Select column for detailed analysis", df.columns)
    
    if selected_column:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Column: {selected_column}**")
            st.write(f"Data Type: {df[selected_column].dtype}")
            st.write(f"Non-null Count: {df[selected_column].notna().sum()}")
            st.write(f"Null Count: {df[selected_column].isna().sum()}")
            st.write(f"Unique Values: {df[selected_column].nunique()}")
            
        with col2:
            if df[selected_column].dtype in ['object', 'string']:
                st.write("**Top Values:**")
                top_values = df[selected_column].value_counts().head(10)
                st.dataframe(top_values)
            elif df[selected_column].dtype in ['int64', 'float64']:
                st.write("**Statistics:**")
                stats = df[selected_column].describe()
                st.dataframe(stats)

def display_raw_data(df):
    """Display raw data with filtering options."""
    
    st.subheader("📋 Raw Data Viewer")
    
    # Data filtering
    col1, col2, col3 = st.columns(3)
    
    with col1:
        show_rows = st.number_input("Number of rows to display", 
                                  min_value=10, max_value=1000, value=100)
    
    with col2:
        start_row = st.number_input("Start from row", 
                                  min_value=0, max_value=len(df)-1, value=0)
    
    with col3:
        # Column selection
        selected_columns = st.multiselect(
            "Select columns (empty = all)", 
            df.columns.tolist(),
            default=[]
        )
    
    # Apply filters
    end_row = min(start_row + show_rows, len(df))
    df_display = df.iloc[start_row:end_row]
    
    if selected_columns:
        df_display = df_display[selected_columns]
    
    # Display data
    st.dataframe(df_display, use_container_width=True)
    
    # Download button
    csv = df_display.to_csv(index=False)
    st.download_button(
        label="📥 Download displayed data as CSV",
        data=csv,
        file_name=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def display_no_data_message():
    """Display message when no data is available."""
    
    st.info("🔄 No processed data available yet. The pipeline may still be processing data.")
    
    # Show pipeline status
    try:
        redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        
        # Check ingestion status
        sync_status = redis_client.get('sync_status')
        if sync_status:
            sync_data = json.loads(sync_status)
            st.write("**Last Data Ingestion:**", sync_data.get('last_sync', 'Unknown'))
            
        # Check cleaning status
        cleaning_status = redis_client.get('cleaning_status')
        if cleaning_status:
            cleaning_data = json.loads(cleaning_status)
            st.write("**Last Data Cleaning:**", cleaning_data.get('last_cleaning', 'Unknown'))
            
    except Exception as e:
        st.warning("Unable to check pipeline status")
        logger.error(f"Error checking pipeline status: {str(e)}")

if __name__ == "__main__":
    main()
