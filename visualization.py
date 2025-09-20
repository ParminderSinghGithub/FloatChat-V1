"""
Visualization Module for ARGO Float Data

This module handles creating interactive plots and maps for ARGO float
oceanographic data using Plotly and Folium.

In the final SIH PoC, this will be extended with:
- Advanced 3D visualizations
- Real-time data streaming plots
- Machine learning model visualizations
- Custom dashboard layouts
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from typing import List, Dict, Optional, Tuple
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArgoVisualization:
    """Handles visualization of ARGO float data."""
    
    def __init__(self):
        """Initialize the visualization class."""
        self.color_palette = px.colors.qualitative.Set3
    
    def create_profile_plot(self, df: pd.DataFrame, float_id: str, 
                          parameter: str = 'temp') -> go.Figure:
        """
        Create a profile plot (parameter vs depth) for a specific float.
        
        Args:
            df: DataFrame with oceanographic data
            float_id: Float identifier
            parameter: Parameter to plot ('temp' or 'sal')
            
        Returns:
            Plotly figure object
        """
        try:
            # Filter data for specific float
            float_data = df[df['float_id'] == float_id].copy()
            
            if float_data.empty:
                logger.warning(f"No data found for float {float_id}")
                return go.Figure()
            
            # Sort by depth for proper profile visualization
            float_data = float_data.sort_values('depth')
            
            # Create the plot
            fig = go.Figure()
            
            # Group by time to create separate traces for each profile
            for time, profile_data in float_data.groupby('time'):
                if parameter in profile_data.columns and not profile_data[parameter].isna().all():
                    fig.add_trace(go.Scatter(
                        x=profile_data[parameter],
                        y=profile_data['depth'],
                        mode='lines+markers',
                        name=f"{time.strftime('%Y-%m-%d')}",
                        line=dict(width=2),
                        marker=dict(size=4),
                        hovertemplate=f'<b>{parameter.title()}</b>: %{{x}}<br>' +
                                    f'<b>Depth</b>: %{{y}} m<br>' +
                                    f'<b>Date</b>: {time.strftime("%Y-%m-%d")}<br>' +
                                    '<extra></extra>'
                    ))
            
            # Update layout
            fig.update_layout(
                title=f'{parameter.title()} Profile for Float {float_id}',
                xaxis_title=f'{parameter.title()}',
                yaxis_title='Depth (m)',
                yaxis=dict(autorange='reversed'),  # Depth increases downward
                hovermode='closest',
                showlegend=True,
                height=600,
                template='plotly_white'
            )
            
            # Add grid
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            logger.info(f"Created {parameter} profile plot for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating profile plot: {e}")
            return go.Figure()
    
    def create_combined_profile_plot(self, df: pd.DataFrame, float_id: str) -> go.Figure:
        """
        Create a combined profile plot showing both temperature and salinity.
        
        Args:
            df: DataFrame with oceanographic data
            float_id: Float identifier
            
        Returns:
            Plotly figure with subplots
        """
        try:
            # Filter data for specific float
            float_data = df[df['float_id'] == float_id].copy()
            
            if float_data.empty:
                logger.warning(f"No data found for float {float_id}")
                return go.Figure()
            
            # Create subplots
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('Temperature Profile', 'Salinity Profile'),
                horizontal_spacing=0.1
            )
            
            # Sort by depth
            float_data = float_data.sort_values('depth')
            
            # Add temperature profile
            for time, profile_data in float_data.groupby('time'):
                if not profile_data['temp'].isna().all():
                    fig.add_trace(go.Scatter(
                        x=profile_data['temp'],
                        y=profile_data['depth'],
                        mode='lines+markers',
                        name=f"Temp {time.strftime('%Y-%m-%d')}",
                        line=dict(width=2, color='red'),
                        marker=dict(size=4),
                        showlegend=True
                    ), row=1, col=1)
            
            # Add salinity profile
            for time, profile_data in float_data.groupby('time'):
                if not profile_data['sal'].isna().all():
                    fig.add_trace(go.Scatter(
                        x=profile_data['sal'],
                        y=profile_data['depth'],
                        mode='lines+markers',
                        name=f"Sal {time.strftime('%Y-%m-%d')}",
                        line=dict(width=2, color='blue'),
                        marker=dict(size=4),
                        showlegend=True
                    ), row=1, col=2)
            
            # Update layout
            fig.update_layout(
                title=f'Combined Profiles for Float {float_id}',
                height=600,
                template='plotly_white'
            )
            
            # Update axes
            fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
            fig.update_xaxes(title_text="Salinity", row=1, col=2)
            fig.update_yaxes(title_text="Depth (m)", autorange='reversed', row=1, col=1)
            fig.update_yaxes(title_text="Depth (m)", autorange='reversed', row=1, col=2)
            
            # Add grids
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            logger.info(f"Created combined profile plot for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating combined profile plot: {e}")
            return go.Figure()
    
    def create_float_map(self, df: pd.DataFrame) -> folium.Map:
        """
        Create an interactive map showing float locations.
        
        Args:
            df: DataFrame with oceanographic data
            
        Returns:
            Folium map object
        """
        try:
            # Get unique float positions (latest measurement for each float)
            float_positions = df.groupby('float_id').agg({
                'lat': 'last',
                'lon': 'last',
                'time': 'max',
                'depth': 'max',
                'temp': 'mean',
                'sal': 'mean'
            }).reset_index()
            
            if float_positions.empty:
                logger.warning("No float positions found")
                return folium.Map(location=[0, 0], zoom_start=2)
            
            # Calculate map center
            center_lat = float_positions['lat'].mean()
            center_lon = float_positions['lon'].mean()
            
            # Create map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=3,
                tiles='OpenStreetMap'
            )
            
            # Add float markers
            for _, row in float_positions.iterrows():
                # Create popup content
                popup_content = f"""
                <b>Float ID:</b> {row['float_id']}<br>
                <b>Last Update:</b> {row['time'].strftime('%Y-%m-%d')}<br>
                <b>Max Depth:</b> {row['depth']:.0f} m<br>
                <b>Avg Temperature:</b> {row['temp']:.2f}°C<br>
                <b>Avg Salinity:</b> {row['sal']:.2f}<br>
                <b>Coordinates:</b> {row['lat']:.3f}, {row['lon']:.3f}
                """
                
                # Choose marker color based on temperature
                if row['temp'] < 10:
                    color = 'blue'
                elif row['temp'] < 20:
                    color = 'green'
                else:
                    color = 'red'
                
                # Add marker
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"Float {row['float_id']}",
                    icon=folium.Icon(color=color, icon='ship', prefix='fa')
                ).add_to(m)
            
            logger.info(f"Created map with {len(float_positions)} float markers")
            return m
            
        except Exception as e:
            logger.error(f"Error creating float map: {e}")
            return folium.Map(location=[0, 0], zoom_start=2)
    
    def create_parameter_map(self, df: pd.DataFrame, parameter: str = 'temp') -> go.Figure:
        """
        Create a scatter plot map showing parameter values at float locations.
        
        Args:
            df: DataFrame with oceanographic data
            parameter: Parameter to visualize ('temp' or 'sal')
            
        Returns:
            Plotly figure object
        """
        try:
            # Get surface measurements (shallowest depth for each float/time)
            surface_data = df.loc[df.groupby(['float_id', 'time'])['depth'].idxmin()].copy()
            
            if surface_data.empty:
                logger.warning("No surface data found")
                return go.Figure()
            
            # Create scatter plot
            fig = px.scatter_mapbox(
                surface_data,
                lat='lat',
                lon='lon',
                color=parameter,
                size='depth',
                hover_data=['float_id', 'time', 'temp', 'sal'],
                color_continuous_scale='Viridis',
                mapbox_style='open-street-map',
                title=f'{parameter.title()} Distribution at Float Locations',
                height=600
            )
            
            # Update layout
            fig.update_layout(
                mapbox=dict(
                    center=dict(
                        lat=surface_data['lat'].mean(),
                        lon=surface_data['lon'].mean()
                    ),
                    zoom=2
                ),
                margin=dict(r=0, t=40, l=0, b=0)
            )
            
            logger.info(f"Created {parameter} distribution map")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating parameter map: {e}")
            return go.Figure()
    
    def create_time_series_plot(self, df: pd.DataFrame, float_id: str, 
                              parameter: str = 'temp') -> go.Figure:
        """
        Create a time series plot for a specific float and parameter.
        
        Args:
            df: DataFrame with oceanographic data
            float_id: Float identifier
            parameter: Parameter to plot ('temp' or 'sal')
            
        Returns:
            Plotly figure object
        """
        try:
            # Filter data for specific float
            float_data = df[df['float_id'] == float_id].copy()
            
            if float_data.empty:
                logger.warning(f"No data found for float {float_id}")
                return go.Figure()
            
            # Get surface measurements (shallowest depth for each time)
            surface_data = float_data.loc[float_data.groupby('time')['depth'].idxmin()].copy()
            surface_data = surface_data.sort_values('time')
            
            # Create time series plot
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=surface_data['time'],
                y=surface_data[parameter],
                mode='lines+markers',
                name=f'{parameter.title()}',
                line=dict(width=2),
                marker=dict(size=6),
                hovertemplate=f'<b>Date</b>: %{{x}}<br>' +
                            f'<b>{parameter.title()}</b>: %{{y}}<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'{parameter.title()} Time Series for Float {float_id}',
                xaxis_title='Date',
                yaxis_title=f'{parameter.title()}',
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            
            # Add grid
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            logger.info(f"Created {parameter} time series for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating time series plot: {e}")
            return go.Figure()
    
    def create_depth_heatmap(self, df: pd.DataFrame, float_id: str, 
                           parameter: str = 'temp') -> go.Figure:
        """
        Create a depth-time heatmap for a specific float and parameter.
        
        Args:
            df: DataFrame with oceanographic data
            float_id: Float identifier
            parameter: Parameter to visualize ('temp' or 'sal')
            
        Returns:
            Plotly figure object
        """
        try:
            # Filter data for specific float
            float_data = df[df['float_id'] == float_id].copy()
            
            if float_data.empty:
                logger.warning(f"No data found for float {float_id}")
                return go.Figure()
            
            # Create pivot table for heatmap
            pivot_data = float_data.pivot_table(
                values=parameter,
                index='depth',
                columns='time',
                aggfunc='mean'
            )
            
            # Create heatmap
            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale='Viridis',
                hovertemplate=f'<b>Date</b>: %{{x}}<br>' +
                            f'<b>Depth</b>: %{{y}} m<br>' +
                            f'<b>{parameter.title()}</b>: %{{z}}<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'{parameter.title()} Depth-Time Heatmap for Float {float_id}',
                xaxis_title='Date',
                yaxis_title='Depth (m)',
                yaxis=dict(autorange='reversed'),
                height=500,
                template='plotly_white'
            )
            
            logger.info(f"Created {parameter} depth-time heatmap for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating depth heatmap: {e}")
            return go.Figure()
    
    def create_summary_dashboard(self, df: pd.DataFrame) -> go.Figure:
        """
        Create a summary dashboard with multiple plots.
        
        Args:
            df: DataFrame with oceanographic data
            
        Returns:
            Plotly figure with subplots
        """
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Temperature Distribution', 'Salinity Distribution',
                              'Depth Distribution', 'Float Locations'),
                specs=[[{"type": "histogram"}, {"type": "histogram"}],
                       [{"type": "histogram"}, {"type": "scatter"}]]
            )
            
            # Temperature distribution
            fig.add_trace(go.Histogram(
                x=df['temp'].dropna(),
                name='Temperature',
                nbinsx=30,
                marker_color='red'
            ), row=1, col=1)
            
            # Salinity distribution
            fig.add_trace(go.Histogram(
                x=df['sal'].dropna(),
                name='Salinity',
                nbinsx=30,
                marker_color='blue'
            ), row=1, col=2)
            
            # Depth distribution
            fig.add_trace(go.Histogram(
                x=df['depth'],
                name='Depth',
                nbinsx=30,
                marker_color='green'
            ), row=2, col=1)
            
            # Float locations (surface data)
            surface_data = df.loc[df.groupby(['float_id', 'time'])['depth'].idxmin()]
            fig.add_trace(go.Scatter(
                x=surface_data['lon'],
                y=surface_data['lat'],
                mode='markers',
                name='Float Locations',
                marker=dict(size=8, color='purple'),
                text=surface_data['float_id'],
                hovertemplate='<b>Float ID</b>: %{text}<br>' +
                            '<b>Lat</b>: %{y}<br>' +
                            '<b>Lon</b>: %{x}<br>' +
                            '<extra></extra>'
            ), row=2, col=2)
            
            # Update layout
            fig.update_layout(
                title='ARGO Float Data Summary Dashboard',
                height=800,
                showlegend=False,
                template='plotly_white'
            )
            
            # Update axes labels
            fig.update_xaxes(title_text="Temperature (°C)", row=1, col=1)
            fig.update_xaxes(title_text="Salinity", row=1, col=2)
            fig.update_xaxes(title_text="Depth (m)", row=2, col=1)
            fig.update_xaxes(title_text="Longitude", row=2, col=2)
            fig.update_yaxes(title_text="Count", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=2)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            fig.update_yaxes(title_text="Latitude", row=2, col=2)
            
            logger.info("Created summary dashboard")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating summary dashboard: {e}")
            return go.Figure()


def main():
    """Test the visualization functionality."""
    # Create sample data
    from data_ingestion import ArgoDataIngestion
    
    ingestion = ArgoDataIngestion()
    df = ingestion.ingest_sample_data(max_files=2)
    
    # Test visualizations
    viz = ArgoVisualization()
    
    # Test profile plot
    float_id = df['float_id'].iloc[0]
    profile_fig = viz.create_profile_plot(df, float_id, 'temp')
    print(f"Created profile plot for float {float_id}")
    
    # Test combined profile plot
    combined_fig = viz.create_combined_profile_plot(df, float_id)
    print(f"Created combined profile plot for float {float_id}")
    
    # Test float map
    float_map = viz.create_float_map(df)
    print(f"Created float map with {len(df['float_id'].unique())} floats")
    
    # Test summary dashboard
    dashboard_fig = viz.create_summary_dashboard(df)
    print("Created summary dashboard")


if __name__ == "__main__":
    main()
