import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class DataVisualizer:
    """Create various data visualizations using Plotly."""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
        
    def create_correlation_heatmap(self, df):
        """Create a correlation heatmap for numeric columns."""
        try:
            corr_matrix = df.corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0,
                text=np.round(corr_matrix.values, 2),
                texttemplate='%{text}',
                textfont={"size": 10},
                hovertemplate='%{x} vs %{y}<br>Correlation: %{z}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Correlation Heatmap",
                xaxis_title="Variables",
                yaxis_title="Variables",
                height=600,
                width=800
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating correlation heatmap: {str(e)}")
    
    def create_histogram(self, df, column):
        """Create a histogram for a numeric column."""
        try:
            fig = px.histogram(
                df, 
                x=column,
                nbins=30,
                title=f"Distribution of {column}",
                labels={column: column.title().replace('_', ' ')},
                marginal="box"
            )
            
            fig.update_layout(
                showlegend=False,
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating histogram: {str(e)}")
    
    def create_box_plot(self, df, column):
        """Create a box plot for a numeric column."""
        try:
            fig = px.box(
                df,
                y=column,
                title=f"Box Plot of {column}",
                labels={column: column.title().replace('_', ' ')}
            )
            
            fig.update_layout(
                showlegend=False,
                height=400
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating box plot: {str(e)}")
    
    def create_scatter_plot(self, df, x_col, y_col, color_col=None):
        """Create a scatter plot."""
        try:
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col.title()} vs {x_col.title()}",
                labels={
                    x_col: x_col.title().replace('_', ' '),
                    y_col: y_col.title().replace('_', ' ')
                },
                hover_data=[col for col in df.columns if col not in [x_col, y_col, color_col]][:3]
            )
            
            # Add trend line
            if df[x_col].notna().any() and df[y_col].notna().any():
                try:
                    z = np.polyfit(df[x_col].dropna(), df[y_col].dropna(), 1)
                    p = np.poly1d(z)
                    x_trend = np.linspace(df[x_col].min(), df[x_col].max(), 100)
                    
                    fig.add_trace(go.Scatter(
                        x=x_trend,
                        y=p(x_trend),
                        mode='lines',
                        name='Trend Line',
                        line=dict(dash='dash', color='red')
                    ))
                except:
                    pass
            
            fig.update_layout(height=500)
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating scatter plot: {str(e)}")
    
    def create_time_series_plot(self, df, date_col, value_col):
        """Create a time series plot."""
        try:
            # Sort by date
            df_sorted = df.sort_values(date_col)
            
            fig = px.line(
                df_sorted,
                x=date_col,
                y=value_col,
                title=f"{value_col.title()} Over Time",
                labels={
                    date_col: "Date",
                    value_col: value_col.title().replace('_', ' ')
                }
            )
            
            fig.update_layout(
                height=400,
                xaxis_title="Date",
                yaxis_title=value_col.title().replace('_', ' ')
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating time series plot: {str(e)}")
    
    def create_bar_chart(self, df, x_col, y_col=None, orientation='v'):
        """Create a bar chart."""
        try:
            if y_col is None:
                # Create value counts bar chart
                value_counts = df[x_col].value_counts().head(20)
                
                fig = px.bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    title=f"Distribution of {x_col.title()}",
                    labels={
                        'x': x_col.title().replace('_', ' '),
                        'y': 'Count'
                    },
                    orientation=orientation
                )
            else:
                # Create grouped bar chart
                fig = px.bar(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"{y_col.title()} by {x_col.title()}",
                    labels={
                        x_col: x_col.title().replace('_', ' '),
                        y_col: y_col.title().replace('_', ' ')
                    },
                    orientation=orientation
                )
            
            fig.update_layout(height=400)
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating bar chart: {str(e)}")
    
    def create_pie_chart(self, df, column, max_categories=10):
        """Create a pie chart for categorical data."""
        try:
            value_counts = df[column].value_counts().head(max_categories)
            
            fig = px.pie(
                values=value_counts.values,
                names=value_counts.index,
                title=f"Distribution of {column.title()}",
                labels={'names': column.title().replace('_', ' ')},
                color_discrete_sequence=self.color_palette
            )
            
            fig.update_layout(height=500)
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating pie chart: {str(e)}")
    
    def create_violin_plot(self, df, column, group_by=None):
        """Create a violin plot."""
        try:
            fig = px.violin(
                df,
                y=column,
                x=group_by,
                box=True,
                title=f"Violin Plot of {column.title()}",
                labels={
                    column: column.title().replace('_', ' '),
                    group_by: group_by.title().replace('_', ' ') if group_by else None
                }
            )
            
            fig.update_layout(height=500)
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating violin plot: {str(e)}")
    
    def create_heatmap(self, df, x_col, y_col, value_col):
        """Create a heatmap for three variables."""
        try:
            pivot_df = df.pivot_table(
                values=value_col,
                index=y_col,
                columns=x_col,
                aggfunc='mean'
            )
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns,
                y=pivot_df.index,
                colorscale='Viridis',
                hovertemplate=f'{x_col}: %{{x}}<br>{y_col}: %{{y}}<br>{value_col}: %{{z}}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f"Heatmap: {value_col.title()} by {x_col.title()} and {y_col.title()}",
                xaxis_title=x_col.title().replace('_', ' '),
                yaxis_title=y_col.title().replace('_', ' '),
                height=500
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating heatmap: {str(e)}")
    
    def create_multi_line_chart(self, df, x_col, y_cols, title=None):
        """Create a multi-line chart."""
        try:
            fig = go.Figure()
            
            for i, y_col in enumerate(y_cols):
                fig.add_trace(go.Scatter(
                    x=df[x_col],
                    y=df[y_col],
                    mode='lines',
                    name=y_col.title().replace('_', ' '),
                    line=dict(color=self.color_palette[i % len(self.color_palette)])
                ))
            
            fig.update_layout(
                title=title or f"Multiple Variables Over {x_col.title()}",
                xaxis_title=x_col.title().replace('_', ' '),
                yaxis_title="Values",
                height=500,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                )
            )
            
            return fig
            
        except Exception as e:
            return self._create_error_figure(f"Error creating multi-line chart: {str(e)}")
    
    def _create_error_figure(self, error_message):
        """Create a figure showing an error message."""
        fig = go.Figure()
        
        fig.add_annotation(
            text=error_message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="red")
        )
        
        fig.update_layout(
            title="Visualization Error",
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            height=400
        )
        
        return fig
