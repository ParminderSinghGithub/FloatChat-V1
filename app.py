"""
ARGO Float Data Pipeline - Streamlit Application

This is the main Streamlit application that integrates all components:
- Data ingestion from NetCDF files
- Database storage and querying
- Interactive visualizations
- Natural language chatbot interface

In the final SIH PoC, this will be extended with:
- Real-time data streaming
- Advanced ML model integration
- Multi-user collaboration features
- Custom dashboard configurations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import logging
import os
from pathlib import Path

# Import our custom modules
from data_ingestion import ArgoDataIngestion
from db_utils import ArgoDatabase
from visualization import ArgoVisualization
from chatbot import ArgoChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="ARGO Float Data Pipeline",
    page_icon="🌊",
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
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'float_data' not in st.session_state:
    st.session_state.float_data = pd.DataFrame()
if 'float_summary' not in st.session_state:
    st.session_state.float_summary = pd.DataFrame()


def initialize_data():
    """Initialize data and database."""
    try:
        with st.spinner("Loading ARGO float data..."):
            # Initialize data ingestion
            ingestion = ArgoDataIngestion()
            df = ingestion.ingest_sample_data(max_files=3)
            
            if df.empty:
                st.error("No data could be loaded. Please check your data directory.")
                return False
            
            # Initialize database
            with ArgoDatabase() as db:
                db.insert_measurements(df)
                summary = db.get_float_summary()
            
            # Store in session state
            st.session_state.float_data = df
            st.session_state.float_summary = summary
            st.session_state.data_loaded = True
            st.session_state.db_initialized = True
            
            st.success(f"Successfully loaded {len(df)} measurements from {len(df['float_id'].unique())} floats!")
            return True
            
    except Exception as e:
        st.error(f"Error initializing data: {str(e)}")
        return False


def main():
    """Main application function."""
    
    # Header
    st.markdown('<h1 class="main-header">🌊 ARGO Float Data Pipeline</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🚀 Quick Start")
        
        if not st.session_state.data_loaded:
            if st.button("📊 Load Sample Data", type="primary"):
                initialize_data()
        else:
            st.markdown('<div class="success-box">✅ Data loaded successfully!</div>', unsafe_allow_html=True)
            
            # Data summary
            st.markdown("### 📈 Data Summary")
            st.write(f"**Floats:** {len(st.session_state.float_summary)}")
            st.write(f"**Measurements:** {len(st.session_state.float_data)}")
            st.write(f"**Date Range:** {st.session_state.float_data['time'].min().strftime('%Y-%m-%d')} to {st.session_state.float_data['time'].max().strftime('%Y-%m-%d')}")
            
            # Refresh data button
            if st.button("🔄 Refresh Data"):
                st.session_state.data_loaded = False
                st.session_state.db_initialized = False
                st.rerun()
        
        st.markdown("### 📚 About")
        st.markdown("""
        This prototype demonstrates an end-to-end pipeline for ARGO oceanographic float data:
        
        - **Data Ingestion:** NetCDF file processing
        - **Database Storage:** SQLite with query capabilities
        - **Visualizations:** Interactive plots and maps
        - **Chatbot:** Natural language queries
        
        *Built for internal hackathon demonstration*
        """)
    
    # Main content
    if not st.session_state.data_loaded:
        st.markdown("""
        <div class="info-box">
            <h3>Welcome to the ARGO Float Data Pipeline!</h3>
            <p>This prototype demonstrates a complete end-to-end pipeline for oceanographic data analysis.</p>
            <p><strong>Click "Load Sample Data" in the sidebar to get started.</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show architecture diagram
        st.markdown("### 🏗️ Pipeline Architecture")
        st.image("https://via.placeholder.com/800x400/1f77b4/ffffff?text=ARGO+Data+Pipeline", 
                caption="Data Flow: NetCDF → Database → Visualizations → Chatbot")
        
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map", "📊 Profile Plots", "🤖 Chatbot Query"])
    
    with tab1:
        show_interactive_map()
    
    with tab2:
        show_profile_plots()
    
    with tab3:
        show_chatbot_interface()


def show_interactive_map():
    """Show the interactive map tab."""
    st.markdown('<h2 class="section-header">🗺️ Interactive Float Map</h2>', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Create float map
    float_map = viz.create_float_map(st.session_state.float_data)
    
    # Display map
    import streamlit_folium as st_folium
    st_folium.st_folium(float_map, width=700, height=600)
    
    # Map controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 Map Controls")
        show_surface_data = st.checkbox("Show Surface Data Only", value=True)
        
    with col2:
        st.markdown("### 📍 Float Selection")
        selected_float = st.selectbox(
            "Select a float to view details:",
            options=st.session_state.float_summary['float_id'].tolist()
        )
        
    with col3:
        st.markdown("### 📊 Quick Stats")
        if selected_float:
            float_info = st.session_state.float_summary[
                st.session_state.float_summary['float_id'] == selected_float
            ].iloc[0]
            
            st.metric("Total Measurements", int(float_info['total_measurements']))
            st.metric("Max Depth", f"{float_info['max_depth']:.0f}m")
            st.metric("Avg Temperature", f"{float_info['avg_temp']:.2f}°C")
    
    # Show selected float details
    if selected_float:
        st.markdown(f"### 📋 Details for Float {selected_float}")
        
        float_data = st.session_state.float_data[
            st.session_state.float_data['float_id'] == selected_float
        ]
        
        if show_surface_data:
            # Show surface data only
            surface_data = float_data.loc[float_data.groupby('time')['depth'].idxmin()]
            st.dataframe(surface_data[['time', 'lat', 'lon', 'depth', 'temp', 'sal']], 
                        use_container_width=True)
        else:
            # Show all data
            st.dataframe(float_data[['time', 'lat', 'lon', 'depth', 'temp', 'sal']], 
                        use_container_width=True)


def show_profile_plots():
    """Show the profile plots tab."""
    st.markdown('<h2 class="section-header">📊 Oceanographic Profiles</h2>', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Float selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🎛️ Plot Controls")
        
        selected_float = st.selectbox(
            "Select Float:",
            options=st.session_state.float_summary['float_id'].tolist(),
            key="profile_float"
        )
        
        plot_type = st.selectbox(
            "Plot Type:",
            options=["Temperature Profile", "Salinity Profile", "Combined Profile", "Time Series", "Depth Heatmap"]
        )
        
        parameter = st.selectbox(
            "Parameter:",
            options=["temp", "sal"],
            key="profile_param"
        )
    
    with col2:
        st.markdown("### 📈 Profile Visualization")
        
        if selected_float:
            # Generate appropriate plot
            if plot_type == "Temperature Profile":
                fig = viz.create_profile_plot(st.session_state.float_data, selected_float, 'temp')
            elif plot_type == "Salinity Profile":
                fig = viz.create_profile_plot(st.session_state.float_data, selected_float, 'sal')
            elif plot_type == "Combined Profile":
                fig = viz.create_combined_profile_plot(st.session_state.float_data, selected_float)
            elif plot_type == "Time Series":
                fig = viz.create_time_series_plot(st.session_state.float_data, selected_float, parameter)
            elif plot_type == "Depth Heatmap":
                fig = viz.create_depth_heatmap(st.session_state.float_data, selected_float, parameter)
            
            if fig and not fig.data:
                st.warning("No data available for the selected float and plot type.")
            else:
                st.plotly_chart(fig, use_container_width=True)
    
    # Summary statistics
    st.markdown("### 📊 Summary Statistics")
    
    if selected_float:
        float_data = st.session_state.float_data[
            st.session_state.float_data['float_id'] == selected_float
        ]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Profiles", len(float_data['time'].unique()))
        
        with col2:
            st.metric("Max Depth", f"{float_data['depth'].max():.0f}m")
        
        with col3:
            st.metric("Avg Temperature", f"{float_data['temp'].mean():.2f}°C")
        
        with col4:
            st.metric("Avg Salinity", f"{float_data['sal'].mean():.2f}")


def show_chatbot_interface():
    """Show the chatbot interface tab."""
    st.markdown('<h2 class="section-header">🤖 Natural Language Query Interface</h2>', unsafe_allow_html=True)
    
    # Initialize chatbot
    with ArgoDatabase() as db:
        chatbot = ArgoChatbot(db)
        
        # Chat interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 💬 Ask a Question")
            
            # Query input
            user_query = st.text_input(
                "Enter your question about the ARGO float data:",
                placeholder="e.g., 'Show me floats near the equator' or 'Find high temperature measurements'",
                key="chatbot_query"
            )
            
            # Process query button
            if st.button("🔍 Search", type="primary"):
                if user_query:
                    with st.spinner("Processing your query..."):
                        results, explanation, suggestion = chatbot.process_query(user_query)
                        
                        # Store results in session state
                        st.session_state.chatbot_results = results
                        st.session_state.chatbot_explanation = explanation
                        st.session_state.chatbot_suggestion = suggestion
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            st.markdown("### 💡 Example Queries")
            
            example_queries = chatbot.suggest_queries()
            for i, example in enumerate(example_queries[:5]):
                if st.button(f"💭 {example}", key=f"example_{i}"):
                    st.session_state.chatbot_query = example
                    st.rerun()
            
            # Help button
            if st.button("❓ Help"):
                st.session_state.show_help = True
        
        # Display results
        if hasattr(st.session_state, 'chatbot_results'):
            st.markdown("### 📋 Query Results")
            
            # Explanation
            st.markdown(f"**Explanation:** {st.session_state.chatbot_explanation}")
            
            # Results table
            if not st.session_state.chatbot_results.empty:
                st.dataframe(st.session_state.chatbot_results, use_container_width=True)
                
                # Visualization of results
                if len(st.session_state.chatbot_results) > 0:
                    st.markdown("### 📊 Results Visualization")
                    
                    # Create a simple scatter plot of float locations
                    fig = px.scatter(
                        st.session_state.chatbot_results,
                        x='min_lon',
                        y='min_lat',
                        color='avg_temp',
                        size='total_measurements',
                        hover_data=['float_id', 'avg_temp', 'avg_sal'],
                        title="Float Locations from Query Results",
                        color_continuous_scale='Viridis'
                    )
                    
                    fig.update_layout(
                        xaxis_title="Longitude",
                        yaxis_title="Latitude",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No results found for your query.")
            
            # Suggestion
            st.markdown(f"**Suggestion:** {st.session_state.chatbot_suggestion}")
        
        # Help section
        if hasattr(st.session_state, 'show_help') and st.session_state.show_help:
            st.markdown("### 📚 Query Help")
            st.markdown(chatbot.get_query_help(), unsafe_allow_html=True)
            
            if st.button("❌ Close Help"):
                st.session_state.show_help = False
                st.rerun()


def show_data_summary():
    """Show data summary in sidebar."""
    if st.session_state.data_loaded:
        st.markdown("### 📊 Data Summary")
        
        # Basic statistics
        st.write(f"**Total Floats:** {len(st.session_state.float_summary)}")
        st.write(f"**Total Measurements:** {len(st.session_state.float_data)}")
        
        # Date range
        min_date = st.session_state.float_data['time'].min()
        max_date = st.session_state.float_data['time'].max()
        st.write(f"**Date Range:** {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
        
        # Depth range
        min_depth = st.session_state.float_data['depth'].min()
        max_depth = st.session_state.float_data['depth'].max()
        st.write(f"**Depth Range:** {min_depth:.0f}m to {max_depth:.0f}m")
        
        # Temperature range
        min_temp = st.session_state.float_data['temp'].min()
        max_temp = st.session_state.float_data['temp'].max()
        st.write(f"**Temperature Range:** {min_temp:.2f}°C to {max_temp:.2f}°C")
        
        # Salinity range
        min_sal = st.session_state.float_data['sal'].min()
        max_sal = st.session_state.float_data['sal'].max()
        st.write(f"**Salinity Range:** {min_sal:.2f} to {max_sal:.2f}")


if __name__ == "__main__":
    main()
