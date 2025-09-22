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
        """Initialize the visualization class with oceanic theme."""
        # Oceanic color palette
        self.oceanic_colors = [
            '#0B1426',  # Ocean deep
            '#1B2951',  # Ocean dark
            '#2E4F7C',  # Ocean medium
            '#4A90A4',  # Ocean light
            '#7BC3D4',  # Ocean surface
            '#88D8C0',  # Ocean wave
            '#A8E6CF',  # Ocean foam
            '#FF6B6B'   # Coral accent
        ]
        self.color_palette = self.oceanic_colors
        
        # Visualization types supported
        self.visualization_types = [
            '🌡️ Temperature Profile',
            '🧂 Salinity Profile',
            '🌊 Combined Profile',
            '📊 Depth Distribution',
            '📈 Parameter Histogram'
        ]
        
        # Oceanic theme settings
        self.oceanic_theme = {
            'paper_bgcolor': 'rgba(11, 20, 38, 0.8)',
            'plot_bgcolor': 'rgba(27, 41, 81, 0.6)',
            'font_color': '#FEFEFE',
            'grid_color': 'rgba(123, 195, 212, 0.3)',
            'line_color': '#7BC3D4'
        }
    
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
            
            # Check if parameter data is available
            has_data = False
            if parameter in float_data.columns and not float_data[parameter].isna().all():
                has_data = True
                fig.add_trace(go.Scatter(
                    x=float_data[parameter],
                    y=float_data['depth'],
                    mode='lines+markers',
                    name=f"Float {float_id}",
                    line=dict(width=2),
                    marker=dict(size=4),
                    hovertemplate=f'<b>{parameter.title()}</b>: %{{x}}<br>' +
                                f'<b>Depth</b>: %{{y}} m<br>' +
                                f'<b>Float ID</b>: {float_id}<br>' +
                                '<extra></extra>'
                ))
            
            # Add "No Data Available" message if no data for this parameter
            if not has_data:
                fig.add_annotation(
                    text=f"{parameter.title()} Data<br>Not Available<br><br>This ARGO float does not<br>measure {parameter.title()}",
                    x=0.5, y=0.5,
                    xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=16, color="gray"),
                    bgcolor="rgba(240,240,240,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                )
            
            # Update layout with oceanic theme
            param_emoji = "🌡️" if parameter == "temp" else "🧂"
            fig.update_layout(
                title=f'{param_emoji} {parameter.title()} Profile - Float {float_id}',
                xaxis_title=f'{param_emoji} {parameter.title()}',
                yaxis_title='🏊‍♀️ Depth (m)',
                yaxis=dict(autorange='reversed'),  # Depth increases downward
                hovermode='closest',
                showlegend=True,
                height=600,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color'])
            )
            
            # Add oceanic grid
            fig.update_xaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            fig.update_yaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            
            logger.info(f"Created {parameter} profile plot for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating profile plot: {e}")
            return go.Figure()
            
    def create_depth_distribution(self, df: pd.DataFrame, bin_size: int = 50) -> go.Figure:
        """
        Create a histogram showing the distribution of sampling depths.
        
        Args:
            df: DataFrame with oceanographic data
            bin_size: Size of depth bins for histogram
            
        Returns:
            Plotly figure object
        """
        try:
            if df.empty or 'depth' not in df.columns:
                logger.warning("No depth data available")
                return go.Figure()
            
            # Create depth bins
            max_depth = df['depth'].max()
            bins = np.arange(0, max_depth + bin_size, bin_size)
            
            # Create the histogram
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                y=df['depth'],
                nbinsy=len(bins)-1,
                name='Depth Distribution',
                marker_color=self.oceanic_colors[3],
                opacity=0.75,
                hovertemplate='<b>Count</b>: %{x}<br>' +
                            '<b>Depth Range</b>: %{y} m<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title='🌊 Depth Distribution of Measurements',
                xaxis_title='Number of Measurements',
                yaxis_title='🏊‍♀️ Depth (m)',
                yaxis=dict(autorange='reversed'),  # Depth increases downward
                height=600,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color']),
                showlegend=False,
                bargap=0.1
            )
            
            # Add oceanic grid
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            
            logger.info("Created depth distribution plot")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating depth distribution plot: {e}")
            return go.Figure()
    
    def create_parameter_histogram(self, df: pd.DataFrame, float_id: str, parameter: str = 'temp') -> go.Figure:
        """
        Create a histogram showing the distribution of a parameter (temperature or salinity).
        
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
            
            if float_data.empty or parameter not in float_data.columns:
                logger.warning(f"No {parameter} data available for float {float_id}")
                return go.Figure()
            
            param_emoji = "🌡️" if parameter == "temp" else "🧂"
            param_name = "Temperature" if parameter == "temp" else "Salinity"
            color = self.oceanic_colors[4] if parameter == "temp" else self.oceanic_colors[6]
            
            # Create histogram with oceanic styling
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=float_data[parameter].dropna(),
                name=f'{param_name} Distribution',
                marker_color=color,
                opacity=0.75,
                hovertemplate='<b>Count</b>: %{y}<br>' +
                            f'<b>{param_name}</b>: %{{x}}<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout
            fig.update_layout(
                title=f'{param_emoji} {param_name} Distribution',
                xaxis_title=f'{param_emoji} {param_name}',
                yaxis_title='Number of Measurements',
                height=600,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color']),
                showlegend=False,
                bargap=0.1
            )
            
            # Add oceanic grid
            fig.update_xaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            fig.update_yaxes(
                showgrid=True,
                gridwidth=1,
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            
            logger.info(f"Created {parameter} histogram plot")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating parameter histogram plot: {e}")
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
            
            # Create oceanic subplots
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=('🌡️ Temperature Profile', '🧂 Salinity Profile'),
                horizontal_spacing=0.1
            )
            
            # Sort by depth
            float_data = float_data.sort_values('depth')
            
            # Add temperature profile
            if not float_data['temp'].isna().all():
                fig.add_trace(go.Scatter(
                    x=float_data['temp'],
                    y=float_data['depth'],
                    mode='lines+markers',
                    name=f"🌡️ Temperature",
                    line=dict(width=3, color=self.oceanic_colors[4]),  # Ocean surface color
                    marker=dict(size=6, color=self.oceanic_colors[5]),  # Ocean wave color
                    showlegend=True
                ), row=1, col=1)
            
            # Add salinity profile (check if data is available)
            has_salinity_data = False
            if not float_data['sal'].isna().all():
                has_salinity_data = True
                fig.add_trace(go.Scatter(
                    x=float_data['sal'],
                    y=float_data['depth'],
                    mode='lines+markers',
                    name=f"🧂 Salinity",
                    line=dict(width=3, color=self.oceanic_colors[6]),  # Ocean foam color
                    marker=dict(size=6, color=self.oceanic_colors[3]),  # Ocean light color
                    showlegend=True
                ), row=1, col=2)
            
            # Add "No Data Available" message if no salinity data
            if not has_salinity_data:
                fig.add_annotation(
                    text="Salinity Data<br>Not Available<br><br>This ARGO float uses<br>auxiliary sensors only",
                    xref="x2", yref="y2",
                    x=0.5, y=0.5,
                    xanchor='center', yanchor='middle',
                    showarrow=False,
                    font=dict(size=14, color="gray"),
                    bgcolor="rgba(240,240,240,0.8)",
                    bordercolor="gray",
                    borderwidth=1
                )
            
            # Update layout with oceanic theme
            fig.update_layout(
                title=f'🌊 Ocean Profiles - Float {float_id}',
                height=600,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color'])
            )
            
            # Update axes with oceanic styling
            fig.update_xaxes(title_text="🌡️ Temperature (°C)", row=1, col=1, 
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_xaxes(title_text="🧂 Salinity", row=1, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="🏊‍♀️ Depth (m)", autorange='reversed', row=1, col=1,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="🏊‍♀️ Depth (m)", autorange='reversed', row=1, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            
            # Add oceanic grids
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=self.oceanic_theme['grid_color'])
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=self.oceanic_theme['grid_color'])
            
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
            # Get unique float positions (average position for each float)
            float_positions = df.groupby('float_id').agg({
                'lat': 'mean',
                'lon': 'mean',
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
            
            # Create oceanic map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=3,
                tiles='CartoDB dark_matter'  # Dark oceanic theme
            )
            
            # Add float markers
            for _, row in float_positions.iterrows():
                # Create oceanic popup content with real ARGO float information
                popup_content = f"""
                <div style="font-family: Inter, sans-serif; color: #0B1426;">
                <h4 style="color: #2E4F7C; margin-bottom: 10px;">🌊 ARGO Float {row['float_id']}</h4>
                <p><strong>🏊‍♀️ Max Depth:</strong> {row['depth']:.0f} m</p>
                <p><strong>🌡️ Avg Temperature:</strong> {row['temp']:.2f}°C</p>
                <p><strong>🧂 Avg Salinity:</strong> {row['sal']:.2f}</p>
                <p><strong>📍 Location:</strong> {row['lat']:.4f}°, {row['lon']:.4f}°</p>
                <p><strong>🌊 Source:</strong> Real ARGO Dataset</p>
                </div>
                """
                
                # Choose oceanic marker color based on temperature
                if row['temp'] < 10:
                    color = 'blue'  # Cold deep ocean
                elif row['temp'] < 20:
                    color = 'lightblue'  # Moderate ocean
                else:
                    color = 'orange'  # Warm surface
                
                # Add oceanic marker with real ARGO float ID
                folium.Marker(
                    [row['lat'], row['lon']],
                    popup=folium.Popup(popup_content, max_width=350),
                    tooltip=f"🌊 ARGO Float {row['float_id']} (Real Ocean Data)",
                    icon=folium.Icon(color=color, icon='tint', prefix='fa')
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
            # Get surface measurements (shallowest depth for each float)
            surface_data = df.loc[df.groupby('float_id')['depth'].idxmin()].copy()
            
            if surface_data.empty:
                logger.warning("No surface data found")
                return go.Figure()
            
            # Create oceanic scatter plot
            param_emoji = "🌡️" if parameter == "temp" else "🧂"
            fig = px.scatter_mapbox(
                surface_data,
                lat='lat',
                lon='lon',
                color=parameter,
                size='depth',
                hover_data=['float_id', 'depth', 'temp', 'sal'],
                color_continuous_scale='Blues',  # Oceanic color scale
                mapbox_style='carto-darkmatter',  # Dark oceanic theme
                title=f'{param_emoji} {parameter.title()} Distribution - Ocean Surface',
                height=600
            )
            
            # Update layout with oceanic theme
            fig.update_layout(
                mapbox=dict(
                    center=dict(
                        lat=surface_data['lat'].mean(),
                        lon=surface_data['lon'].mean()
                    ),
                    zoom=2
                ),
                margin=dict(r=0, t=40, l=0, b=0),
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color'])
            )
            
            logger.info(f"Created {parameter} distribution map")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating parameter map: {e}")
            return go.Figure()
    
    def create_depth_distribution_plot(self, df: pd.DataFrame, float_id: str, 
                              parameter: str = 'temp') -> go.Figure:
        """
        Create a depth distribution plot for a specific float and parameter.
        
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
            
            # Sort by depth
            float_data = float_data.sort_values('depth')
            
            # Create depth distribution plot
            fig = go.Figure()
            
            param_emoji = "🌡️" if parameter == "temp" else "🧂"
            fig.add_trace(go.Scatter(
                x=float_data['depth'],
                y=float_data[parameter],
                mode='lines+markers',
                name=f'{param_emoji} {parameter.title()}',
                line=dict(width=3, color=self.oceanic_colors[4]),  # Ocean surface color
                marker=dict(size=6, color=self.oceanic_colors[5]),  # Ocean wave color
                hovertemplate=f'<b>🏊‍♀️ Depth</b>: %{{x}} m<br>' +
                            f'<b>{param_emoji} {parameter.title()}</b>: %{{y}}<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout with oceanic theme
            fig.update_layout(
                title=f'{param_emoji} {parameter.title()} vs Depth Distribution - Float {float_id}',
                xaxis_title='🏊‍♀️ Depth (m)',
                yaxis_title=f'{param_emoji} {parameter.title()}',
                hovermode='x unified',
                height=400,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color'])
            )
            
            # Add oceanic grid
            fig.update_xaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            fig.update_yaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            
            logger.info(f"Created {parameter} depth distribution for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating depth distribution plot: {e}")
            return go.Figure()
    
    def create_parameter_histogram(self, df: pd.DataFrame, float_id: str, 
                           parameter: str = 'temp') -> go.Figure:
        """
        Create a parameter distribution histogram for a specific float.
        
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
            
            # Create parameter histogram
            param_emoji = "🌡️" if parameter == "temp" else "🧂"
            fig = go.Figure(data=go.Histogram(
                x=float_data[parameter].dropna(),
                nbinsx=30,
                marker_color=self.oceanic_colors[4],  # Ocean surface color
                name=f'{param_emoji} {parameter.title()}',
                hovertemplate=f'<b>{param_emoji} {parameter.title()}</b>: %{{x}}<br>' +
                            f'<b>Count</b>: %{{y}}<br>' +
                            '<extra></extra>'
            ))
            
            # Update layout with oceanic theme
            fig.update_layout(
                title=f'{param_emoji} {parameter.title()} Distribution - Float {float_id}',
                xaxis_title=f'{param_emoji} {parameter.title()}',
                yaxis_title='🔢 Frequency',
                height=400,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=18, color=self.oceanic_theme['font_color'])
            )
            
            # Add oceanic grid
            fig.update_xaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            fig.update_yaxes(
                showgrid=True, 
                gridwidth=1, 
                gridcolor=self.oceanic_theme['grid_color'],
                linecolor=self.oceanic_theme['line_color']
            )
            
            logger.info(f"Created {parameter} histogram for float {float_id}")
            return fig
            
        except Exception as e:
            logger.error(f"Error creating parameter histogram: {e}")
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
            # Create oceanic subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('🌡️ Temperature Distribution', '🧂 Salinity Distribution',
                              '🏊‍♀️ Depth Distribution', '🗺️ Float Locations'),
                specs=[[{"type": "histogram"}, {"type": "histogram"}],
                       [{"type": "histogram"}, {"type": "scatter"}]]
            )
            
            # Temperature distribution with oceanic colors
            fig.add_trace(go.Histogram(
                x=df['temp'].dropna(),
                name='🌡️ Temperature',
                nbinsx=30,
                marker_color=self.oceanic_colors[4]  # Ocean surface color
            ), row=1, col=1)
            
            # Salinity distribution with oceanic colors
            fig.add_trace(go.Histogram(
                x=df['sal'].dropna(),
                name='🧂 Salinity',
                nbinsx=30,
                marker_color=self.oceanic_colors[6]  # Ocean foam color
            ), row=1, col=2)
            
            # Depth distribution with oceanic colors
            fig.add_trace(go.Histogram(
                x=df['depth'],
                name='🏊‍♀️ Depth',
                nbinsx=30,
                marker_color=self.oceanic_colors[2]  # Ocean medium color
            ), row=2, col=1)
            
            # Float locations (surface data) with oceanic styling
            surface_data = df.loc[df.groupby('float_id')['depth'].idxmin()]
            fig.add_trace(go.Scatter(
                x=surface_data['lon'],
                y=surface_data['lat'],
                mode='markers',
                name='🗺️ Float Locations',
                marker=dict(size=10, color=self.oceanic_colors[5], 
                          line=dict(width=2, color=self.oceanic_colors[0])),
                text=surface_data['float_id'],
                hovertemplate='<b>🌊 Float ID</b>: %{text}<br>' +
                            '<b>📍 Lat</b>: %{y}<br>' +
                            '<b>📍 Lon</b>: %{x}<br>' +
                            '<extra></extra>'
            ), row=2, col=2)
            
            # Update layout with oceanic theme
            fig.update_layout(
                title='🌊 Ocean Data Summary Dashboard',
                height=800,
                showlegend=False,
                paper_bgcolor=self.oceanic_theme['paper_bgcolor'],
                plot_bgcolor=self.oceanic_theme['plot_bgcolor'],
                font=dict(color=self.oceanic_theme['font_color'], family='Inter'),
                title_font=dict(size=20, color=self.oceanic_theme['font_color'])
            )
            
            # Update axes labels with oceanic emojis
            fig.update_xaxes(title_text="🌡️ Temperature (°C)", row=1, col=1,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_xaxes(title_text="🧂 Salinity", row=1, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_xaxes(title_text="🏊‍♀️ Depth (m)", row=2, col=1,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_xaxes(title_text="🧭 Longitude", row=2, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="Count", row=1, col=1,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="Count", row=1, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="Count", row=2, col=1,
                           linecolor=self.oceanic_theme['line_color'])
            fig.update_yaxes(title_text="🧭 Latitude", row=2, col=2,
                           linecolor=self.oceanic_theme['line_color'])
            
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
