import threading
import sqlite3
from contextlib import contextmanager
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import logging
import os
from pathlib import Path
import time

# Import our custom modules
from data_ingestion import ArgoDataIngestion
from db_utils import ArgoDatabase
from visualization import ArgoVisualization
from chatbot import ArgoChatbot

_thread_locals = threading.local()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Interface Functions 
def show_chatbot_interface():
    """Show the oceanic AI assistant interface tab."""
    
    # Initialize session state for example query execution
    if 'execute_example_query' not in st.session_state:
        st.session_state.execute_example_query = None
    
    # Initialize chatbot
    with ArgoDatabase() as db:
        chatbot = ArgoChatbot(db)
        
        # Chat interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Add vertical spacing to center content
            st.markdown('<div style="padding-top: 4rem;"></div>', unsafe_allow_html=True)
            
            # Center the search container content
            st.markdown('''
            <div style="display: flex; flex-direction: column; align-items: center; max-width: 600px; margin: 0 auto;">
            ''', unsafe_allow_html=True)
            
            st.markdown('''
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                    🐙 Ask the Ocean AI
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            # Set default value for query input based on example selection
            default_query = st.session_state.execute_example_query if st.session_state.execute_example_query else ""
            
            # Oceanic query input
            user_query = st.text_input(
                "🌊 What would you like to know about the ocean data?",
                value=default_query,
                placeholder="e.g., 'Show me floats near the equator' or 'Find warm ocean currents'",
                key="chatbot_query_input"
            )
            
            # Auto-execute if example query was selected
            should_execute = st.button("🌊 Dive Deep", type="primary") or st.session_state.execute_example_query is not None
            
            # Process query
            if should_execute:
                if user_query:
                    with st.spinner("Processing your query..."):
                        results, explanation, suggestion = chatbot.process_query(user_query)
                        
                        # Store results in session state
                        st.session_state.chatbot_results = results
                        st.session_state.chatbot_explanation = explanation
                        st.session_state.chatbot_suggestion = suggestion
                        
                        # Clear the example query flag
                        st.session_state.execute_example_query = None
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            st.markdown('''
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                    🐠 Ocean Query Examples
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            # Example queries
            example_queries = chatbot.suggest_queries()
            oceanic_emojis = ["🌊", "🐠", "🐙", "🦈", "🐋"]
            for i, example in enumerate(example_queries[:5]):
                emoji = oceanic_emojis[i % len(oceanic_emojis)]
                if st.button(f"{emoji} {example}", key=f"example_{i}"):
                    # Set the example query to be executed
                    st.session_state.execute_example_query = example
                    st.rerun()
            
            # Oceanic help button
            if st.button("🐙 Ocean Guide"):
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

def show_profile_plots():
    """Show the oceanic profile plots tab."""
    st.markdown('''
    <h2 style="color: #000000 !important; font-weight: 900 !important; font-family: Arial, sans-serif !important; text-shadow: none !important; -webkit-text-fill-color: #000000 !important;">🌊 Ocean Depth Profiles</h2>
    ''', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Float selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Add vertical spacing to center content
        st.markdown('<div style="padding-top: 8rem;"></div>', unsafe_allow_html=True)
        
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                🌊 Ocean Controls
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        # Initialize visualization
        viz = ArgoVisualization()
        
        selected_float = st.selectbox(
            "🏝️ Select Ocean Float:",
            options=st.session_state.float_summary['float_id'].tolist(),
            key="profile_float"
        )
        
        plot_type = st.selectbox(
            "📊 Visualization Type:",
            options=viz.visualization_types
        )
        
        # Only show parameter selection for plots that use it
        if plot_type in ["📈 Parameter Histogram"]:
            parameter = st.selectbox(
                "🔬 Ocean Parameter:",
                options=["temp", "sal"],
                format_func=lambda x: "🌡️ Temperature" if x == "temp" else "🧂 Salinity", 
                key="profile_param"
            )
        else:
            # Set default parameter based on plot type
            if plot_type == "🌡️ Temperature Profile":
                parameter = "temp"
            elif plot_type == "🧂 Salinity Profile":
                parameter = "sal"
            # For other plots, parameter doesn't matter
    
    with col2:
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                📈 Profile Visualization
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        if selected_float:
            float_data = get_float_data_from_db_fast(selected_float)
            
            if float_data.empty:
                st.warning("No data available for this float.")
                return
            
            # Data availability check
            has_temp = not float_data['temp'].isna().all()
            has_sal = not float_data['sal'].isna().all()
            
            # Show data availability warnings
            if (plot_type == "🧂 Salinity Profile" or 
                (parameter == "sal" and plot_type in ["📊 Depth Distribution", "📈 Parameter Histogram"])) and not has_sal:
                st.warning("⚠️ Salinity data not available for this float.")
            
            # Generate plots based on selection
            if plot_type == "🌡️ Temperature Profile":
                fig = viz.create_profile_plot(float_data, selected_float, 'temp')
            elif plot_type == "🧂 Salinity Profile":
                fig = viz.create_profile_plot(float_data, selected_float, 'sal')
            elif plot_type == "🌊 Combined Profile":
                fig = viz.create_combined_profile_plot(float_data, selected_float)
            elif plot_type == "📊 Depth Distribution":
                fig = viz.create_depth_distribution(float_data)
            elif plot_type == "📈 Parameter Histogram":
                fig = viz.create_parameter_histogram(float_data, selected_float, parameter)
            
            if fig and not fig.data:
                st.warning("No data available for the selected plot type.")
            elif fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Please select a valid plot type.")

            # Show data details
            st.markdown("### ⚓ Float Data Details")
            
            if not float_data.empty:
                # Add surface data toggle
                show_surface_data = st.checkbox("🏄‍♀️ Show Surface Data Only", 
                                              value=True, 
                                              key="profile_surface_toggle")
                
                if show_surface_data:
                    surface_data = float_data.loc[float_data.groupby(['lat', 'lon'])['depth'].idxmin()]
                    st.dataframe(surface_data[['lat', 'lon', 'depth', 'temp', 'sal']], 
                              use_container_width=True)
                else:
                    st.dataframe(float_data[['lat', 'lon', 'depth', 'temp', 'sal']], 
                              use_container_width=True)

def show_interactive_map():
    """Show the interactive oceanic map tab."""
    st.markdown('''
    <h2 style="color: #000000 !important; font-weight: 900 !important; font-family: Arial, sans-serif !important; text-shadow: none !important; -webkit-text-fill-color: #000000 !important;">🗺️ Ocean Explorer Map</h2>
    ''', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Layout: Map takes more space, controls take less
    map_col, controls_col = st.columns([3, 1])
    
    # Initialize selected_float from session state or default
    if 'selected_map_float' not in st.session_state:
        st.session_state.selected_map_float = st.session_state.float_summary['float_id'].iloc[0]
    
    with controls_col:
        # Professional Float Selection
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                🏝️ Float Selection
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        selected_float = st.selectbox(
            "Select Ocean Float:",
            options=st.session_state.float_summary['float_id'].tolist(),
            key="map_float_selection"
        )
        
        # Update map float in session state
        st.session_state.selected_map_float = selected_float
    
    with map_col:
        selected_float = st.session_state.selected_map_float
        
        if selected_float:
            # Filter data for selected float only
            selected_float_data = st.session_state.float_data[
                st.session_state.float_data['float_id'] == selected_float
            ]
            
            # Create map with only the selected float
            float_map = viz.create_float_map(selected_float_data)
            
            # Display map
            import streamlit_folium as st_folium
            st_folium.st_folium(float_map, width=700, height=600)
        else:
            st.info("Please select a float to view on the map.")

def get_thread_safe_db_instance():
    """Get or create a thread-safe ArgoDatabase instance."""
    if not hasattr(_thread_locals, 'db_instance') or _thread_locals.db_instance is None:
        try:
            # Create new ArgoDatabase instance for this thread
            db = ArgoDatabase()
            # Apply ultra-fast optimizations
            if hasattr(db, 'connection') and db.connection:
                db.connection.execute("PRAGMA cache_size = 500000")  # 500MB cache
                db.connection.execute("PRAGMA temp_store = MEMORY")
                db.connection.execute("PRAGMA mmap_size = 2147483648")  # 2GB memory mapping
                db.connection.execute("PRAGMA busy_timeout = 60000")  # 60 second timeout
                db.connection.execute("PRAGMA synchronous = NORMAL")
                db.connection.execute("PRAGMA journal_mode = WAL")
                db.connection.execute("PRAGMA page_size = 4096")
                db.connection.execute("PRAGMA optimize")
            
            _thread_locals.db_instance = db
            print(f"Created thread-safe ArgoDatabase instance in thread {threading.get_ident()}")
            return db
        except Exception as e:
            print(f"Failed to create ArgoDatabase instance: {e}")
            return None
    
    return _thread_locals.db_instance

@contextmanager
def get_db_context_ultra_fast():
    """Ultra-fast context manager that works with your ArgoDatabase class."""
    db = get_thread_safe_db_instance()
    try:
        yield db
    except Exception as e:
        print(f"Database operation failed: {e}")
        raise


@st.cache_resource
def get_optimized_database_connection():
    """Backward compatibility wrapper - uses thread-safe connection."""
    return get_thread_safe_db_instance()

@st.cache_data(ttl=600, max_entries=1)  # Cache for 10 minutes, only 1 entry
def get_database_stats_ultra_fast():
    """Ultra-fast database stats using your existing backend with thread safety."""
    try:
        with get_db_context_ultra_fast() as db:
            if db and hasattr(db, 'connection') and db.connection:
                cursor = db.connection.cursor()
                
                # Try to get approximate count from sqlite_stat1 (ultra-fast)
                try:
                    cursor.execute("SELECT stat FROM sqlite_stat1 WHERE tbl='argo_measurements' AND idx IS NULL")
                    result = cursor.fetchone()
                    
                    if result:
                        total_measurements = int(result[0])
                    else:
                        # Ultra-fast sampling estimation
                        cursor.execute("""
                            SELECT COUNT(*) FROM (
                                SELECT 1 FROM argo_measurements 
                                WHERE rowid % 1000 = 0 
                                LIMIT 1000
                            )
                        """)
                        sample_count = cursor.fetchone()[0]
                        total_measurements = sample_count * 1000
                except:
                    # Fallback to basic sampling
                    cursor.execute("SELECT COUNT(*) FROM argo_measurements WHERE rowid % 100 = 0 LIMIT 10000")
                    sample_count = cursor.fetchone()[0]
                    total_measurements = sample_count * 100
                
                # Fast unique float count approximation
                cursor.execute("SELECT COUNT(DISTINCT float_id) FROM argo_measurements WHERE rowid % 100 = 0")
                unique_floats = cursor.fetchone()[0] * 100
                
                # Database size from file system (instant)
                db_size_bytes = Path("argo_data.db").stat().st_size
                db_size_mb = db_size_bytes / (1024 * 1024)
                
                return {
                    'total_measurements': total_measurements,
                    'unique_floats': unique_floats,
                    'database_size_mb': db_size_mb
                }
        return {}
    except Exception as e:
        print(f"Error getting database stats: {e}")
        return {'error': str(e)}



@st.cache_data(ttl=600, max_entries=1)  # Cache for 10 minutes
def get_float_summary_ultra_fast():
    """Ultra-fast float summary using your existing backend with thread safety."""
    try:
        with get_db_context_ultra_fast() as db:
            if db and hasattr(db, 'connection') and db.connection:
                # Ultra-efficient query with intelligent sampling
                query = """
                SELECT 
                    float_id,
                    COUNT(*) * 50 as total_measurements,  -- Multiply by sampling factor
                    MIN(lat) as min_lat,
                    MAX(lat) as max_lat,
                    MIN(lon) as min_lon,
                    MAX(lon) as max_lon,
                    MAX(depth) as max_depth,
                    AVG(temp) as avg_temp,
                    AVG(sal) as avg_sal
                FROM (
                    SELECT * FROM argo_measurements 
                    WHERE rowid % 50 = 0  -- Sample every 50th row for ultra speed
                ) 
                GROUP BY float_id
                ORDER BY total_measurements DESC
                LIMIT 100  -- Top 100 floats only
                """
                return pd.read_sql_query(query, db.connection)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting float summary: {e}")
        return pd.DataFrame()


def get_sample_data_ultra_fast(limit=25000):  # Reduced from 50000 for speed
    """Ultra-fast sample data using your existing backend with thread safety."""
    try:
        with get_db_context_ultra_fast() as db:
            if db and hasattr(db, 'connection') and db.connection:
                # Ultra-intelligent sampling for geographic distribution
                query = """
                WITH sampled_data AS (
                    SELECT 
                        float_id, lat, lon, depth, temp, sal,
                        ROW_NUMBER() OVER (
                            PARTITION BY 
                                ROUND(lat, 1),  -- Grid by 0.1 degrees
                                ROUND(lon, 1)
                            ORDER BY RANDOM()
                        ) as rn
                    FROM argo_measurements 
                    WHERE lat IS NOT NULL AND lon IS NOT NULL
                    AND rowid % 20 = 0  -- Pre-sample for ultra speed
                )
                SELECT float_id, lat, lon, depth, temp, sal
                FROM sampled_data 
                WHERE rn <= 2  -- Max 2 points per grid cell
                ORDER BY RANDOM()
                LIMIT ?
                """
                return pd.read_sql_query(query, db.connection, params=[limit])
        return pd.DataFrame()
    except Exception as e:
        print(f"Error getting sample data: {e}")
        return pd.DataFrame()

# Page configuration with oceanic theme
st.set_page_config(
    page_title="FloatChat",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load oceanic theme CSS
def load_oceanic_theme():
    """Load the oceanic theme CSS styling."""
    try:
        with open('oceanic_theme.css', 'r') as f:
            css_content = f.read()
        st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # Light oceanic theme CSS with maximum text visibility
        st.markdown("""
        <style>
            /* Global override for ALL text - maximum visibility */
            *, *::before, *::after {
                color: #000000 !important;
                font-weight: 900 !important;
                -webkit-text-fill-color: #000000 !important;
                text-shadow: none !important;
                opacity: 1 !important;
            }
            
            /* Override any CSS that might make text invisible */
            html, body, div, span, h1, h2, h3, h4, h5, h6, p, a, 
            strong, em, small, sub, sup, b, i, u, s, strike, 
            blockquote, pre, code, kbd, samp, var, cite, dfn, 
            abbr, acronym, address, big, del, ins, q, tt, 
            dl, dt, dd, ol, ul, li, fieldset, form, label, 
            legend, table, caption, tbody, tfoot, thead, tr, 
            th, td, article, aside, canvas, details, embed, 
            figure, figcaption, footer, header, hgroup, menu, 
            nav, output, ruby, section, summary, time, mark, 
            audio, video, button, input, select, textarea {
                color: #000000 !important;
                font-weight: 900 !important;
                -webkit-text-fill-color: #000000 !important;
            }
            :root {
                --ocean-deep: #1E3A5F;
                --ocean-dark: #2C5F7C;
                --ocean-medium: #4A90A4;
                --ocean-light: #7BC3D4;
                --ocean-surface: #FFFFFF;
                --ocean-foam: #FFFFFF;
                --ocean-wave: #88D8C0;
                --coral-accent: #FF6B6B;
                --pearl-white: #FFFFFF;
                --text-dark: #000000;
                --text-medium: #1F2937;
                --text-light: #374151;
                --sea-glass: #FFFFFF;
                --surface-gradient: #FFFFFF;
                --ocean-gradient: #FFFFFF;
                --card-gradient: #FFFFFF;
            }
            
            .stApp {
                background: #FFFFFF !important;
                font-family: 'Inter', sans-serif !important;
                color: #000000 !important;
            }
            
            .main .block-container {
                background: #FFFFFF !important;
                min-height: 100vh;
                padding: 2rem 1rem;
            }
            
            .main-header {
                font-family: 'Arial', sans-serif !important;
                font-size: 3rem !important;
                font-weight: 900 !important;
                color: #000000 !important;
                text-align: center !important;
                margin-bottom: 2rem !important;
                text-shadow: none !important;
                animation: none !important;
                letter-spacing: 0 !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
                text-rendering: optimizeLegibility !important;
            }
            
            @keyframes wave {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-5px); }
            }
            
            .section-header {
                font-family: 'Arial', sans-serif !important;
                font-size: 1.8rem !important;
                color: #000000 !important;
                margin-top: 2rem !important;
                margin-bottom: 1rem !important;
                border-bottom: 2px solid #88D8C0;
                padding-bottom: 0.5rem;
                text-shadow: none !important;
                font-weight: 900 !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
            }
            
            .info-box {
                background: #FFFFFF !important;
                border: 2px solid #88D8C0 !important;
                padding: 1.5rem !important;
                border-radius: 8px !important;
                margin: 1rem 0 !important;
                box-shadow: none !important;
                color: #000000 !important;
            }
            
            .success-box {
                background: #FFFFFF !important;
                border: 2px solid #88D8C0 !important;
                padding: 1.5rem !important;
                border-radius: 8px !important;
                margin: 1rem 0 !important;
                border-left: 4px solid #88D8C0 !important;
                box-shadow: none !important;
                color: #000000 !important;
            }
            
            .warning-box {
                background: linear-gradient(135deg, rgba(255, 107, 107, 0.1), rgba(255, 193, 7, 0.1));
                backdrop-filter: blur(10px);
                border: 1px solid var(--coral-accent);
                padding: 1.5rem !important;
                border-radius: 15px !important;
                margin: 1rem 0 !important;
                border-left: 4px solid var(--coral-accent) !important;
                box-shadow: 0 4px 16px rgba(44, 95, 124, 0.1);
                color: var(--text-dark);
            }
            
            .stTabs [data-baseweb="tab-list"] {
                background: #FFFFFF !important;
                border: 2px solid #88D8C0 !important;
                border-radius: 8px !important;
                padding: 0.5rem;
                margin-bottom: 2rem;
                box-shadow: none !important;
            }
            
            .stTabs [data-baseweb="tab"] {
                background: transparent !important;
                color: #000000 !important;
                border-radius: 4px !important;
                font-weight: 700 !important;
                transition: none !important;
                border: none !important;
                font-family: 'Arial', sans-serif !important;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: #F0F9FF !important;
                color: #000000 !important;
                transform: none !important;
            }
            
            .stTabs [aria-selected="true"] {
                background: #88D8C0 !important;
                color: #000000 !important;
                font-weight: 900 !important;
                box-shadow: none !important;
            }
            
            .stButton > button {
                background: #88D8C0 !important;
                color: #000000 !important;
                border: 2px solid #88D8C0 !important;
                border-radius: 8px !important;
                padding: 0.75rem 2rem !important;
                font-weight: 900 !important;
                transition: none !important;
                box-shadow: none !important;
                font-family: 'Arial', sans-serif !important;
            }
            
            .stButton > button:hover {
                transform: none !important;
                box-shadow: none !important;
                background: #7BC3D4 !important;
                color: #000000 !important;
            }
            
            .css-1d391kg {
                background: #FFFFFF !important;
                border-right: 2px solid #88D8C0 !important;
            }
            
            .markdown-text-container {
                color: #000000 !important;
            }
            
            .stTextInput > div > div > input {
                background: #FFFFFF !important;
                border: 2px solid #88D8C0 !important;
                border-radius: 8px !important;
                color: #000000 !important;
                padding: 1rem !important;
                font-weight: 700 !important;
                font-family: 'Arial', sans-serif !important;
            }
            
            .stTextInput > div > div > input:focus {
                border-color: #7BC3D4 !important;
                box-shadow: none !important;
                outline: 2px solid #7BC3D4 !important;
            }
            
            .stSelectbox > div > div {
                background: #FFFFFF !important;
                border: 2px solid #88D8C0 !important;
                border-radius: 8px !important;
            }
            
            .stDataFrame {
                background: #FFFFFF !important;
                border-radius: 8px !important;
                overflow: hidden;
                box-shadow: none !important;
                border: 2px solid #88D8C0 !important;
            }
            
            /* Light theme metric cards */
            .stMetric {
                background: #FFFFFF !important;
                border-radius: 8px !important;
                padding: 1rem !important;
                border: 2px solid #88D8C0 !important;
                box-shadow: none !important;
            }
            
            /* Force ALL text to be black and bold */
            .stMarkdown, .stText, p, span, div, label, h1, h2, h3, h4, h5, h6, 
            .stTabs [data-baseweb="tab"], .stButton button, .stSelectbox, 
            .stTextInput, .element-container, .stMetric, .metric-container,
            [data-testid="stMarkdownContainer"], [data-testid="stText"],
            .css-1d391kg, .css-1d391kg *, .main *, .block-container *,
            .stApp *, .streamlit-container *, .stHeader *, .stSidebar * {
                color: #000000 !important;
                font-weight: 900 !important;
                font-family: 'Arial', sans-serif !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
                text-rendering: optimizeLegibility !important;
            }
            
            /* Sidebar styling */
            .css-1d391kg .markdown-text-container {
                color: #000000 !important;
            }
            
            /* Remove ALL effects that could cause blur */
            * {
                backdrop-filter: none !important;
                filter: none !important;
                text-shadow: none !important;
                box-shadow: none !important;
                transform: none !important;
                transition: none !important;
                animation: none !important;
                -webkit-font-smoothing: antialiased !important;
                -moz-osx-font-smoothing: grayscale !important;
                text-rendering: optimizeLegibility !important;
            }
            
            /* Force crisp rendering */
            .stApp * {
                image-rendering: -webkit-optimize-contrast !important;
                image-rendering: crisp-edges !important;
            }
            
            /* Target specific Streamlit elements */
            [data-testid="stHeader"] h1,
            [data-testid="stHeader"] h2,
            [data-testid="stHeader"] h3,
            [data-testid="stMarkdownContainer"] *,
            [data-testid="stText"] *,
            .stTabs [data-baseweb="tab"] *,
            .css-1kyxreq *,
            .css-12oz5g7 *,
            .css-1dp5vir *,
            .element-container *,
            .stMarkdown *,
            .markdown-text-container *,
            .stSelectbox label,
            .stTextInput label,
            .stButton label,
            .stMetric label,
            .stMetric div {
                color: #000000 !important;
                font-weight: 900 !important;
                font-family: 'Arial', sans-serif !important;
                text-shadow: none !important;
                opacity: 1 !important;
            }
            
            /* Override Streamlit's default text colors */
            .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3,
            .css-1d391kg p, .css-1d391kg span, .css-1d391kg div,
            .main h1, .main h2, .main h3, .main p, .main span, .main div {
                color: #000000 !important;
                font-weight: 900 !important;
            }
            
            /* Force black text on all interactive elements */
            button, input, select, textarea, label {
                color: #000000 !important;
                font-weight: 900 !important;
            }
            
            /* Target section headers specifically */
            .section-header, .section-header *,
            h1.section-header, h2.section-header, h3.section-header,
            [class*="section-header"], [class*="section-header"] *,
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
            .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
                color: #000000 !important;
                font-weight: 900 !important;
                font-family: 'Arial', sans-serif !important;
                text-shadow: none !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #000000 !important;
                background-clip: unset !important;
                -webkit-background-clip: unset !important;
            }
            
            /* Override any gradient text effects */
            .main-header, .main-header *,
            h1, h2, h3, h4, h5, h6 {
                background: none !important;
                background-image: none !important;
                -webkit-background-clip: unset !important;
                -webkit-text-fill-color: #000000 !important;
                color: #000000 !important;
                font-weight: 900 !important;
            }
            
            /* Force visibility on all possible text containers */
            .css-1629p8f *, .css-1kyxreq *, .css-12oz5g7 *,
            .css-1dp5vir *, .css-1v0mbdj *, .css-18e3th9 *,
            .css-1d391kg *, .css-k1vhr4 *, .css-1y4p8pa *,
            .element-container *, .stMarkdown *, .markdown-text-container * {
                color: #000000 !important;
                font-weight: 900 !important;
                opacity: 1 !important;
                text-shadow: none !important;
            }
            
            /* Float ID buttons styling */
            [data-testid="stHorizontalBlock"] div[data-testid="column"] > div {
                background-color: var(--ocean-deep) !important;
                border-color: var(--ocean-dark) !important;
                color: var(--ocean-foam) !important;
            }
            
            [data-testid="stHorizontalBlock"] div[data-testid="column"] button {
                color: var(--ocean-foam) !important;
            }
            
            [data-testid="stHorizontalBlock"] div[data-testid="column"] p {
                color: var(--ocean-foam) !important;
                font-weight: 500 !important;
            }
            
            /* Ultra-high specificity override for Streamlit */
            .stApp .main .block-container .element-container .stMarkdown h1,
            .stApp .main .block-container .element-container .stMarkdown h2,
            .stApp .main .block-container .element-container .stMarkdown h3,
            .stApp .main .block-container .element-container .stMarkdown h4,
            .stApp .main .block-container .element-container .stMarkdown h5,
            .stApp .main .block-container .element-container .stMarkdown h6,
            .stApp .main .block-container .element-container .stMarkdown p,
            .stApp .main .block-container .element-container .stMarkdown span,
            .stApp .main .block-container .element-container .stMarkdown div {
                color: #000000 !important;
                font-weight: 900 !important;
                -webkit-text-fill-color: #000000 !important;
                text-shadow: none !important;
                opacity: 1 !important;
                background: none !important;
                background-image: none !important;
                -webkit-background-clip: unset !important;
                background-clip: unset !important;
            }
        </style>
        
        <script>
        // Force all text to be black using JavaScript
        function forceBlackText() {
            const allElements = document.querySelectorAll('*');
            allElements.forEach(element => {
                if (element.tagName && (
                    element.tagName.match(/^H[1-6]$/) || 
                    element.tagName === 'P' || 
                    element.tagName === 'SPAN' || 
                    element.tagName === 'DIV' ||
                    element.tagName === 'LABEL' ||
                    element.tagName === 'BUTTON'
                )) {
                    element.style.color = '#000000';
                    element.style.fontWeight = '900';
                    element.style.webkitTextFillColor = '#000000';
                    element.style.textShadow = 'none';
                    element.style.opacity = '1';
                }
            });
        }
        
        // Run immediately and on DOM changes
        forceBlackText();
        setTimeout(forceBlackText, 100);
        setTimeout(forceBlackText, 500);
        setTimeout(forceBlackText, 1000);
        
        // Observer for dynamic content
        const observer = new MutationObserver(forceBlackText);
        observer.observe(document.body, { childList: true, subtree: true });
        </script>
        """, unsafe_allow_html=True)

# Apply oceanic theme
load_oceanic_theme()

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False
if 'float_data' not in st.session_state:
    st.session_state.float_data = pd.DataFrame()
if 'float_summary' not in st.session_state:
    st.session_state.float_summary = pd.DataFrame()


def check_existing_database_ultra_fast():
    """Ultra-fast + thread-safe database check using your existing backend."""
    try:
        db_path = Path("argo_data.db")
        if not db_path.exists():
            print("Database file does not exist")
            return False
            
        db_size_mb = db_path.stat().st_size / (1024 * 1024)
        print(f"Database file size: {db_size_mb:.1f} MB")
        
        if db_size_mb < 100:  # For your 13GB file, this should pass
            print("Database file too small")
            return False
        
        # Use your existing ArgoDatabase class
        try:
            with get_db_context_ultra_fast() as db:
                if db and hasattr(db, 'connection') and db.connection:
                    cursor = db.connection.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='argo_measurements'")
                    if cursor.fetchone():
                        print("Database table exists and appears valid")
                        return True
                    else:
                        print("Database table not found")
                        return False
                else:
                    print("Could not establish database connection")
                    return False
        except Exception as e:
            print(f"Database context failed: {e}")
            return False
                
    except Exception as e:
        print(f"Database check failed: {e}")
        return False



def load_data_from_database_ultra_fast():
    """Ultra-fast data loading using your existing backend with thread safety."""
    try:
        # Get summary with ultra-fast caching
        summary = get_float_summary_ultra_fast()
        if summary.empty:
            print("No float summary available")
            return None, None, None
        
        # Get smaller sample for ultra speed
        sample_data = get_sample_data_ultra_fast(25000)
        if sample_data.empty:
            print("No sample data available")
            return None, None, None
        
        # Quick region determination
        lat_center = sample_data['lat'].mean()
        lon_center = sample_data['lon'].mean()
        
        if -180 <= lon_center <= -30:
            region = "Pacific Ocean"
        elif -30 <= lon_center <= 60:
            region = "Atlantic Ocean"  
        elif 60 <= lon_center <= 180:
            region = "Indian/Pacific Ocean"
        else:
            region = "Global Ocean"
        
        print(f"Ultra-fast loading complete from {region}")
        return sample_data, summary, region
        
    except Exception as e:
        print(f"Error loading data from database: {e}")
        return None, None, None

# CRITICAL FIX: Use your existing ArgoDatabase.get_float_profile method
@st.cache_data(ttl=300, max_entries=50)  # Cache up to 50 different floats
def get_float_data_from_db_ultra_fast(float_id: str) -> pd.DataFrame:
    """Ultra-fast float data loading using your existing backend method."""
    try:
        print(f"Loading float {float_id} using ArgoDatabase.get_float_profile method")
        
        with get_db_context_ultra_fast() as db:
            if db:
                # Use your existing get_float_profile method
                if hasattr(db, 'get_float_profile'):
                    df = db.get_float_profile(float_id)
                    if not df.empty:
                        print(f"Successfully loaded {len(df)} records for float {float_id}")
                        
                        # If too much data, intelligently sample it
                        if len(df) > 15000:
                            print(f"Sampling large dataset ({len(df)} records)")
                            # Sample by depth intervals for better representation
                            df['depth_bin'] = pd.cut(df['depth'], bins=50, duplicates='drop')
                            sampled_df = df.groupby('depth_bin').apply(
                                lambda x: x.sample(n=min(10, len(x))) if len(x) > 0 else x
                            ).reset_index(drop=True)
                            sampled_df = sampled_df.drop('depth_bin', axis=1)
                            print(f"Sampled down to {len(sampled_df)} records")
                            return sampled_df
                        else:
                            return df
                    else:
                        print(f"No data returned for float {float_id}")
                        return pd.DataFrame()
                else:
                    # Fallback to direct query if method doesn't exist
                    print("get_float_profile method not found, using direct query")
                    query = """
                    SELECT float_id, lat, lon, depth, temp, sal
                    FROM argo_measurements 
                    WHERE float_id = ?
                    ORDER BY depth
                    """
                    return pd.read_sql_query(query, db.connection, params=[float_id])
            else:
                print("Could not get database instance")
                return pd.DataFrame()
                
    except Exception as e:
        print(f"Error loading float {float_id}: {e}")
        return pd.DataFrame()
def auto_initialize_data_ultra_fast():
    """Ultra-fast data initialization with thread safety for 13GB database."""
    if not st.session_state.data_loaded:
        # Show immediate loading message
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>🚀 Ultra-Fast Loading from 13GB Database...</h3>
            <p>Thread-safe optimized using your existing backend</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Ultra-fast database check
        if check_existing_database_ultra_fast():
            # Load with ultra-fast functions
            df, summary, region = load_data_from_database_ultra_fast()
            if df is not None and summary is not None and region is not None:
                st.session_state.float_data = df
                st.session_state.float_summary = summary
                st.session_state.region = region
                st.session_state.data_loaded = True
                st.session_state.db_initialized = True
                
                # Clear the loading message once data is loaded
                loading_placeholder.empty()
                return True

        loading_placeholder.error("❌ Could not load database efficiently")
        # Clear error message after 2 seconds
        time.sleep(2)
        loading_placeholder.empty()
        return False
 
@st.cache_resource
def get_optimized_database_connection():
    """Backward compatibility - works with your existing ArgoDatabase class."""
    return get_thread_safe_db_instance()

def get_database_stats_cached():
    """Backward compatibility - redirects to ultra-fast version."""
    return get_database_stats_ultra_fast()

def get_float_summary_cached():
    """Backward compatibility - redirects to ultra-fast version."""
    return get_float_summary_ultra_fast()

def get_float_data_from_db(float_id: str):
    """Backward compatibility - redirects to ultra-fast version."""
    return get_float_data_from_db_ultra_fast(float_id)
       
def initialize_data():
    """Initialize real ARGO float data and database - OPTIMIZED."""
    try:
        # First check if we already have data in the database
        if check_existing_database_ultra_fast():
            print("Loading data from existing database...")
            df, summary, region = load_data_from_database_ultra_fast()
            if df is not None and summary is not None and region is not None:
                # Store in session state
                st.session_state.float_data = df
                st.session_state.float_summary = summary
                st.session_state.region = region
                st.session_state.data_loaded = True
                st.session_state.db_initialized = True
                print(f"Successfully loaded existing data: {len(summary)} floats from {region}")
                return True

        # If no existing data, run the ingestion process
        print("No existing database found. Running data ingestion...")
        # Initialize data ingestion from real ARGO dataset
        ingestion = ArgoDataIngestion()
        df = ingestion.ingest_all_data()

        if df.empty:
            st.error("No ARGO data could be loaded from the dataset.")
            return False

        # Determine region from the data
        lat_center = df['lat'].mean()
        lon_center = df['lon'].mean()

        if -180 <= lon_center <= -30:
            region = "Pacific Ocean"
        elif -30 <= lon_center <= 60:
            region = "Atlantic Ocean"
        elif 60 <= lon_center <= 180:
            region = "Indian/Pacific Ocean"
        else:
            region = "Global Ocean"

        # Store region info
        st.session_state.region = region

        # Initialize database with chunked insertion
        db = get_optimized_database_connection()
        if db:
            # Use chunked insertion for better performance
            db.insert_measurements_chunked(df)
            summary = db.get_float_summary()
        else:
            st.error("Could not connect to database")
            return False

        # Store sample in session state instead of full data
        sample_data = df.sample(n=min(50000, len(df)))
        st.session_state.float_data = sample_data
        st.session_state.float_summary = summary
        st.session_state.data_loaded = True
        st.session_state.db_initialized = True

        print(f"Successfully created new database with {len(df)} measurements from {len(summary)} floats")
        return True

    except Exception as e:
        st.error(f"Error loading ARGO data: {str(e)}")
        return False

# ULTRA-FAST INITIALIZATION FUNCTION
def auto_initialize_data_ultra_fast():
    """Ultra-fast data initialization for 13GB database."""
    if not st.session_state.data_loaded:
        # Show immediate loading message
        loading_placeholder = st.empty()
        loading_placeholder.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>🚀 Quick Loading from 13GB Database...</h3>
            <p>Optimized for large datasets - please wait a moment</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick database check
        if check_existing_database_ultra_fast():
            # Load with optimized functions
            df, summary, region = load_data_from_database_ultra_fast()
            if df is not None and summary is not None and region is not None:
                st.session_state.float_data = df
                st.session_state.float_summary = summary
                st.session_state.region = region
                st.session_state.data_loaded = True
                st.session_state.db_initialized = True
                
                loading_placeholder.success(f"✅ Loaded {len(summary)} floats from {region} (Sample: {len(df):,} measurements)")
                return True
        
        loading_placeholder.error("❌ Could not load database efficiently")
        return False

def get_database_stats_cached():
    """Backward compatibility - redirects to ultra-fast version."""
    return get_database_stats_ultra_fast()

def get_float_summary_cached():
    """Backward compatibility - redirects to ultra-fast version."""
    return get_float_summary_ultra_fast()

def get_float_data_from_db(float_id: str):
    """Backward compatibility - redirects to ultra-fast version."""
    return get_float_data_from_db_ultra_fast(float_id)
    

def main():
    """Main application function."""
    
    # Auto-initialize data on first load
    auto_initialize_data_ultra_fast()
    
    # Oceanic header
    st.markdown(f'''
    <div class="wave-decoration">
        <h1 style="color: #000000 !important; font-weight: 900 !important; font-family: Arial, sans-serif !important; text-shadow: none !important; -webkit-text-fill-color: #000000 !important; text-align: center; font-size: 3rem; margin-bottom: 2rem;">🌊 FloatChat 🐠</h1>
    </div>
    ''', unsafe_allow_html=True)
    
    # Oceanic Sidebar
    with st.sidebar:
        # Ocean Dashboard header
        st.markdown('''
        <div style="text-align: center; margin-bottom: 1rem;">
            <h2 style="color: #7BC3D4; font-family: 'Poppins', sans-serif;">🌊 Ocean Dashboard</h2>
        </div>
        ''', unsafe_allow_html=True)
        
        # Add custom CSS just for float ID selector
        st.markdown('''
        <style>
        /* Float ID selector tags styling */
        [data-baseweb="tag"] {
            background-color: #2C5F7C !important;
            color: white !important;
            border: none !important;
        }
        [data-baseweb="tag"]:hover {
            background-color: #4A90A4 !important;
        }
        /* Close button in tags */
        [data-baseweb="tag"] button {
            color: white !important;
        }
        </style>
        ''', unsafe_allow_html=True)
        
        if st.session_state.data_loaded:
            try:
                # Available regions
                regions = ["All Oceans", "Pacific Ocean", "Atlantic Ocean", "Indian/Pacific Ocean", "Global Ocean"]
                selected_region = st.selectbox("� Select Region", regions, index=0)
                
                # Float ID selection below region
                float_ids = st.session_state.float_summary['float_id'].tolist()
                
                # Filter float IDs based on selected region
                if selected_region != "All Oceans":
                    float_data = st.session_state.float_data
                    if selected_region == "Pacific Ocean":
                        region_floats = float_data[(-180 <= float_data['lon']) & (float_data['lon'] <= -30)]['float_id'].unique()
                    elif selected_region == "Atlantic Ocean":
                        region_floats = float_data[(-30 <= float_data['lon']) & (float_data['lon'] <= 60)]['float_id'].unique()
                    elif selected_region == "Indian/Pacific Ocean":
                        region_floats = float_data[(60 <= float_data['lon']) & (float_data['lon'] <= 180)]['float_id'].unique()
                    else:  # Global Ocean
                        region_floats = float_ids
                    
                    float_ids = [fid for fid in float_ids if fid in region_floats]
                
                selected_floats = st.multiselect("🏝️ Select Float IDs", float_ids, 
                                               default=float_ids[:min(5, len(float_ids))])
                
                # Filter data based on selected float IDs
                filtered_data = st.session_state.float_data[st.session_state.float_data['float_id'].isin(selected_floats)]
                
                # Show statistics section header
                st.markdown("### 📊 Ocean Statistics")
                
                # Number of floats info
                st.markdown(f"**🚢 Selected Floats:** {len(selected_floats):,}")
                
                if not filtered_data.empty:
                    # Coordinate ranges with oceanic styling
                    lat_range = f"{filtered_data['lat'].min():.1f}° to {filtered_data['lat'].max():.1f}°"
                    lon_range = f"{filtered_data['lon'].min():.1f}° to {filtered_data['lon'].max():.1f}°"
                    st.markdown(f"**🧭 Latitude:** {lat_range}")
                    st.markdown(f"**🧭 Longitude:** {lon_range}")
                    
                    # Depth range info
                    depth_range = f"{filtered_data['depth'].min():.0f}m to {filtered_data['depth'].max():.0f}m"
                    st.markdown(f"**🏊‍♀️ Depth Range:** {depth_range}")
                else:
                    st.warning("Please select at least one float to view statistics")
                
            except Exception as e:
                st.warning(f"Error updating dashboard: {str(e)[:30]}...")

    # Main content - data is automatically loaded
    if not st.session_state.data_loaded:
        st.markdown("""
        <div class="info-box loading-ocean">
            <div style="text-align: center;">
                <h3>🌊 Diving into Ocean Data...</h3>
                <p>🐠 Please wait while we explore the depths of authentic ARGO oceanographic data 🐠</p>
                <div style="font-size: 2rem; margin: 1rem 0;">🌊 〰️ 🐋 〰️ 🌊</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Create oceanic tabs
    tab1, tab2, tab3 = st.tabs(["🐙 Ocean AI Assistant", "🌊 Depth Profiles", "🗺️ Ocean Explorer Map"])
    
    with tab1:
        show_chatbot_interface()
    
    with tab2:
        show_profile_plots()
    
    with tab3:
        show_interactive_map()

def show_interactive_map():
    """Show the interactive oceanic map tab."""
    st.markdown('''
    <h2 style="color: #000000 !important; font-weight: 900 !important; font-family: Arial, sans-serif !important; text-shadow: none !important; -webkit-text-fill-color: #000000 !important;">🗺️ Ocean Explorer Map</h2>
    ''', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Layout: Map takes more space, controls take less
    map_col, controls_col = st.columns([3, 1])
    
    # Initialize selected_float from session state or default
    if 'selected_map_float' not in st.session_state:
        st.session_state.selected_map_float = st.session_state.float_summary['float_id'].iloc[0]
    
    with controls_col:
        # Professional Float Selection
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                🏝️ Float Selection
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        selected_float = st.selectbox(
            "Select ARGO Float:",
            options=st.session_state.float_summary['float_id'].tolist(),
            key="map_float_selection_right",
            help="Choose an ARGO float to view its location and statistics",
            index=st.session_state.float_summary['float_id'].tolist().index(st.session_state.selected_map_float)
        )
        
        # Update session state when selection changes
        if selected_float != st.session_state.selected_map_float:
            st.session_state.selected_map_float = selected_float
            st.rerun()
        
        # Professional Ocean Analytics (right below Float Selection)
        st.markdown('''
        <div style="margin-top: 2rem; margin-bottom: 1rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 1rem;">
                📊 Ocean Analytics
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        if selected_float:
            float_info = st.session_state.float_summary[
                st.session_state.float_summary['float_id'] == selected_float
            ].iloc[0]
            
            # Professional metrics using Streamlit components with full labels
            st.markdown("""
            <style>
            [data-testid="stMetricLabel"] {
                overflow: visible !important;
                white-space: normal !important;
                height: auto !important;
                min-height: 3rem !important;
                font-size: 0.85rem !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            [data-testid="metric-container"] {
                padding: 0.25rem !important;
                width: 100% !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Use a single column for metrics to give more width
            st.metric(
                label="📊 Total Measurements",
                value=f"{int(float_info['total_measurements']):,}"
            )
            
            st.metric(
                label="🏊‍♀️ Maximum Depth",
                value=f"{float_info['max_depth']:.0f}m"
            )
            
            st.metric(
                label="🌡️ Average Temperature",
                value=f"{float_info['avg_temp']:.1f}°C"
            )
    
    # Add CSS to remove extra spacing
    st.markdown("""
        <style>
        .element-container {
            padding: 0 !important;
        }
        .stMapContainer > div {
            margin: 0 !important;
            padding: 0 !important;
        }
        iframe {
            width: 100% !important;
            min-width: 100% !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    with map_col:
        # Create and display map for selected float only
        selected_float = st.session_state.selected_map_float
        
        if selected_float:
            # Filter data for selected float only
            selected_float_data = st.session_state.float_data[
                st.session_state.float_data['float_id'] == selected_float
            ]
            
            # Create map with only the selected float
            float_map = viz.create_float_map(selected_float_data)
            
            # Display map with full width and improved styling
            import streamlit_folium as st_folium
            
            # Add custom CSS to fix map container
            st.markdown("""
                <style>
                /* Fix map container and remove white box */
                .element-container:has(iframe) {
                    background: transparent !important;
                }
                .stMapContainer, .stMapContainer > div {
                    background: transparent !important;
                }
                iframe {
                    background: transparent !important;
                    border-radius: 0 !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            st_folium.st_folium(
                float_map, 
                width="100%",
                height=600,
                returned_objects=[],
                feature_group_to_add=None
            )
        else:
            st.info("Please select a float to view on the map.")

# Thread-safe float data retrieval with smart sampling
@st.cache_data(ttl=300)
def get_float_data_from_db_fast(float_id: str) -> pd.DataFrame:
    """Get float data efficiently using simple sampling based on record count."""
    try:
        with get_db_context_ultra_fast() as db:
            if not db or not hasattr(db, 'connection'):
                st.error(f"No valid database connection for float {float_id}")
                return pd.DataFrame()

            # First get a quick count
            cursor = db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM argo_measurements WHERE float_id = ?", [float_id])
            count = cursor.fetchone()[0]

            # Determine sampling rate based on count
            if count > 50000:
                sample_rate = 20
            elif count > 25000:
                sample_rate = 10
            elif count > 10000:
                sample_rate = 5
            else:
                sample_rate = 1

            # Simple, efficient sampling query
            query = """
            SELECT float_id, lat, lon, depth, temp, sal 
            FROM argo_measurements 
            WHERE float_id = ? AND rowid % ? = 0
            ORDER BY depth
            """
            
            df = pd.read_sql_query(query, db.connection, params=[float_id, sample_rate])
            print(f"Retrieved {len(df)} records for float {float_id} (sampling 1/{sample_rate})")
            return df
            
    except Exception as e:
        st.error(f"Error loading float data: {e}")
        return pd.DataFrame()

def show_profile_plots():
    """Show the oceanic profile plots tab - FIXED for no time column."""
    st.markdown('''
    <h2 style="color: #000000 !important; font-weight: 900 !important; font-family: Arial, sans-serif !important; text-shadow: none !important; -webkit-text-fill-color: #000000 !important;">🌊 Ocean Depth Profiles</h2>
    ''', unsafe_allow_html=True)
    
    # Initialize visualization
    viz = ArgoVisualization()
    
    # Float selection
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Add vertical spacing to center content
        st.markdown('<div style="padding-top: 8rem;"></div>', unsafe_allow_html=True)
        
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                🌊 Ocean Controls
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        selected_float = st.selectbox(
            "🏝️ Select Ocean Float:",
            options=st.session_state.float_summary['float_id'].tolist(),
            key="profile_float"
        )
        
        # Initialize visualization
        viz = ArgoVisualization()
        
        plot_type = st.selectbox(
            "📊 Visualization Type:",
            options=viz.visualization_types
        )
        
        # Only show parameter selection for plots that use it
        if plot_type in ["📈 Parameter Histogram"]:
            parameter = st.selectbox(
                "🔬 Ocean Parameter:",
                options=["temp", "sal"],
                format_func=lambda x: "🌡️ Temperature" if x == "temp" else "🧂 Salinity", 
                key="profile_param"
            )
        else:
            # Set default parameter based on plot type
            if plot_type == "🌡️ Temperature Profile":
                parameter = "temp"
            elif plot_type == "🧂 Salinity Profile":
                parameter = "sal"
            else:
                parameter = "temp"  # Default for other profiles
    
    with col2:
        st.markdown('''
        <div style="margin-bottom: 1.5rem;">
            <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                📈 Profile Visualization
            </h3>
        </div>
        ''', unsafe_allow_html=True)
        
        if selected_float:
            # Get float data from database on-demand
            float_data = get_float_data_from_db_fast(selected_float)
            
            if float_data.empty:
                st.warning("No data available for this float.")
                return
            
            # Check data availability for the selected float
            has_temp = not float_data['temp'].isna().all()
            has_sal = not float_data['sal'].isna().all()
            
            # Initialize fig variable
            fig = None
            
            # Show data availability info
            if plot_type == "🧂 Salinity Profile" and not has_sal:
                st.warning("⚠️ Salinity data not available for this float. This ARGO float uses auxiliary sensors that don't measure salinity.")
            elif parameter == "sal" and not has_sal:
                st.warning("⚠️ Salinity data not available for this float.")
            
            # Generate appropriate plot
            if plot_type == "🌡️ Temperature Profile":
                fig = viz.create_profile_plot(float_data, selected_float, 'temp')
            elif plot_type == "🧂 Salinity Profile":
                fig = viz.create_profile_plot(float_data, selected_float, 'sal')
            elif plot_type == "🌊 Combined Profile":
                fig = viz.create_combined_profile_plot(float_data, selected_float)
            elif plot_type == "📊 Depth Distribution":
                fig = viz.create_depth_distribution(float_data)
            elif plot_type == "📈 Parameter Histogram":
                fig = viz.create_parameter_histogram(float_data, selected_float, parameter)
            
            if fig and not fig.data:
                st.warning("No data available for the selected float and plot type.")
            elif fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Please select a valid plot type.")
    
    # Float data table - FIXED: Remove time column references
    st.markdown("### ⚓ Float Data Details")
    
    if selected_float:
        float_data = get_float_data_from_db_fast(selected_float)
        
        if not float_data.empty:
            # Add surface data toggle
            show_surface_data = st.checkbox("🏄‍♀️ Show Surface Data Only", value=True, key="profile_surface_toggle")
            
            if show_surface_data:
                # Show surface data only (minimum depth per location)
                surface_data = float_data.loc[float_data.groupby(['lat', 'lon'])['depth'].idxmin()]
                st.dataframe(surface_data[['lat', 'lon', 'depth', 'temp', 'sal']], 
                            use_container_width=True)
            else:
                # Show all data
                st.dataframe(float_data[['lat', 'lon', 'depth', 'temp', 'sal']], 
                            use_container_width=True)
        else:
            st.warning("No data available for this float.")

def show_chatbot_interface():
    """Show the oceanic AI assistant interface tab."""
    
    # Initialize session state for example query execution
    if 'execute_example_query' not in st.session_state:
        st.session_state.execute_example_query = None
    
    # Initialize chatbot
    with ArgoDatabase() as db:
        chatbot = ArgoChatbot(db)
        
        # Chat interface
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Add vertical spacing to center content
            st.markdown('<div style="padding-top: 4rem;"></div>', unsafe_allow_html=True)
            
            # Center the search container content
            st.markdown('''
            <div style="display: flex; flex-direction: column; align-items: center; max-width: 600px; margin: 0 auto;">
            ''', unsafe_allow_html=True)
            
            st.markdown('''
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                    🐙 Ask the Ocean AI
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            # Set default value for query input based on example selection
            default_query = st.session_state.execute_example_query if st.session_state.execute_example_query else ""
            
            # Oceanic query input
            user_query = st.text_input(
                "🌊 What would you like to know about the ocean data?",
                value=default_query,
                placeholder="e.g., 'Show me floats near the equator' or 'Find warm ocean currents'",
                key="chatbot_query_input"
            )
            
            # Auto-execute if example query was selected
            should_execute = st.button("🌊 Dive Deep", type="primary") or st.session_state.execute_example_query is not None
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Process query
            if should_execute:
                if user_query:
                    with st.spinner("Processing your query..."):
                        results, explanation, suggestion = chatbot.process_query(user_query)
                        
                        # Store results in session state
                        st.session_state.chatbot_results = results
                        st.session_state.chatbot_explanation = explanation
                        st.session_state.chatbot_suggestion = suggestion
                        
                        # Clear the example query flag
                        st.session_state.execute_example_query = None
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            st.markdown('''
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #7BC3D4; font-family: 'Inter', sans-serif; font-weight: 600; margin-bottom: 0.5rem;">
                    🐠 Ocean Query Examples
                </h3>
            </div>
            ''', unsafe_allow_html=True)
            
            example_queries = chatbot.suggest_queries()
            oceanic_emojis = ["🌊", "🐠", "🐙", "🦈", "🐋"]
            for i, example in enumerate(example_queries[:5]):
                emoji = oceanic_emojis[i % len(oceanic_emojis)]
                if st.button(f"{emoji} {example}", key=f"example_{i}"):
                    # Set the example query to be executed
                    st.session_state.execute_example_query = example
                    st.rerun()
            
            # Oceanic help button
            if st.button("🐙 Ocean Guide"):
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
