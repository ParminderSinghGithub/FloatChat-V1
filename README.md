# ARGO Float Data Pipeline - Hackathon Prototype

A comprehensive data analysis pipeline for ARGO oceanographic float data, featuring automated data processing, interactive visualizations, and natural language querying capabilities.

## 🌊 Overview

This project implements a complete data pipeline from NetCDF file ingestion to interactive visualizations and natural language querying. Each component has been carefully designed to handle oceanographic data efficiently while providing an intuitive user interface.

## 🔍 Detailed Component Overview

### Data Ingestion Module (`data_ingestion.py`)
- **NetCDF Processing**: Uses `xarray` for efficient handling of multi-dimensional scientific data
  - Why xarray? Provides labeled arrays and built-in support for NetCDF format
  - Handles missing data gracefully with NumPy masked arrays
- **Sample Data Generation**:
  - Creates realistic test data for development and demonstration
  - Implements Gaussian processes for temperature and salinity profiles
  - Uses actual ARGO float trajectories for realistic spatial distribution

### Database Management (`db_utils.py`)
- **SQLite Implementation**:
  - Why SQLite? Lightweight, serverless, and perfect for self-contained applications
  - WAL (Write-Ahead Logging) mode for improved concurrency
  - Transaction management for data integrity
- **Key Functions**:
  - `create_connection()`: Thread-safe database connections
  - `insert_float_data()`: Optimized bulk data insertion
  - `get_float_data()`: Efficient data retrieval with parameterized queries
  - `validate_database()`: Ensures data integrity and repairs if needed

## 🚀 Features

### 1. Data Ingestion
- NetCDF file processing with xarray
- Support for ARGO float metadata and technical data
- Automatic sample data generation for demonstration
- Extracts: TEMP, PSAL, PRES, LAT, LON, TIME

### 2. Database Storage
- SQLite database with optimized schema
- Indexed queries for performance
- Support for date ranges, bounding boxes, and parameter filters
- Float metadata tracking

### 3. Visualization System (`visualization.py`)
- **Core Visualization Classes**:
  - `ArgoVisualization`: Main class handling all plot types
    - Why class-based? Maintains state and configuration between plots
    - Enables consistent styling and interactive features
- **Plot Types and Their Purpose**:
  - `create_profile_plot()`: Temperature/Salinity vs Depth
    - Uses Plotly for interactive zooming and hovering
    - Supports multiple profiles for comparison
  - `create_map_view()`: Float locations and trajectories
    - Folium integration for interactive maps
    - Clustering for better visualization of dense data
  - `create_time_series()`: Parameter evolution over time
    - Moving averages for trend analysis
    - Confidence intervals for uncertainty visualization
  - `create_depth_heatmap()`: Parameter distribution by depth
    - Uses interpolation for continuous representation
    - Custom colorscales for oceanographic parameters
  - `create_parameter_histogram()`: Statistical distribution analysis
    - Kernel density estimation for smooth distributions
    - Automatic bin size optimization

### 4. Natural Language Interface (`chatbot.py`)
- **Query Processing Engine**:
  - Rule-based system with fuzzy matching
  - Context-aware query interpretation
  - Handles temporal and spatial queries naturally
- **Key Components**:
  - `process_query()`: Main query processing pipeline
    - Tokenization and entity recognition
    - Query validation and reformation
  - `generate_response()`: Natural language response generation
    - Context-aware response formatting
    - Includes relevant metadata and confidence scores
  - `suggest_queries()`: Intelligent query suggestions
    - Based on available data and common patterns
    - Helps users explore data effectively

## 🛠️ Technology Stack and Design Decisions

### Core Technologies
- **Python 3.8+**
  - Why? Modern features, strong scientific computing ecosystem
  - Extensive library support for oceanographic data analysis
  
- **Streamlit**
  - Why? Rapid prototyping of data applications
  - Built-in support for scientific visualizations
  - Easy deployment and configuration
  - Reactive programming model for real-time updates

- **xarray/netCDF4**
  - Why? Native support for labeled multi-dimensional arrays
  - Direct NetCDF file handling
  - Integration with scientific Python ecosystem
  - Efficient memory management for large datasets

- **pandas**
  - Why? Powerful data manipulation capabilities
  - Integration with SQL databases
  - Time series functionality
  - Efficient data filtering and aggregation

- **SQLite3**
  - Why? Self-contained database
  - Zero-configuration required
  - ACID compliance for data integrity
  - Excellent performance for read-heavy workloads

- **Plotly**
  - Why? Interactive visualizations
  - Publication-quality plots
  - Customizable for oceanographic data
  - WebGL support for large datasets

- **Folium**
  - Why? Interactive map visualizations
  - Built on Leaflet.js for reliability
  - Custom marker clustering
  - Multiple map layer support

## 📁 Project Structure and Component Interaction

```
project/
├── app.py                 # Main Streamlit application
│   ├── Session State     # Manages user session data
│   ├── UI Components    # Custom Streamlit widgets
│   └── Page Router     # Handles multi-page navigation
│
├── data_ingestion.py     # NetCDF data processing
│   ├── DataLoader      # Handles file reading
│   ├── DataCleaner    # Data validation and cleaning
│   └── SampleGenerator # Test data generation
│
├── db_utils.py          # Database operations
│   ├── Connection Pool # Thread-safe DB connections
│   ├── Query Builder  # SQL query construction
│   └── Data Validators # Integrity checking
│
├── visualization.py     # Plot and map generation
│   ├── ArgoVisualization # Main visualization class
│   ├── ColorScales     # Custom color schemes
│   └── PlotUtilities   # Helper functions
│
├── chatbot.py          # Natural language processing
│   ├── QueryProcessor  # Query understanding
│   ├── ResponseGenerator # Answer formatting
│   └── ContextManager   # Maintains conversation state
│
├── oceanic_theme.css    # Custom styling
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

Each component is designed to be modular and reusable, with clear interfaces between modules. The architecture follows SOLID principles and emphasizes maintainability and extensibility.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
streamlit run app.py
```

### 3. Access the Interface

Open your browser to `http://localhost:8501`

## 📊 Usage Guide and Features

### Data Management
1. **Loading Data**
   - Use "Load Sample Data" for demonstration
   - Automatic data validation and cleaning
   - Progress tracking during data loading
   - Data integrity verification

2. **Database Operations**
   - Automatic index optimization
   - Transaction-based data updates
   - Efficient query execution
   - Data versioning support

### Interactive Map Features
- **Float Location Visualization**
  - Marker clustering for dense regions
  - Color-coded by parameter values
  - Trajectory visualization options
  - Custom layer controls

- **Data Selection**
  - Rectangle/circle selection tools
  - Time range filtering
  - Parameter-based filtering
  - Saved selection states

### Analysis Tools
- **Profile Analysis**
  - Temperature/Salinity profiles
  - Depth-averaged statistics
  - Anomaly detection
  - Trend analysis

- **Time Series Features**
  - Moving averages
  - Seasonal decomposition
  - Outlier detection
  - Correlation analysis

- **Statistical Tools**
  - Parameter distributions
  - Confidence intervals
  - Summary statistics
  - Data quality metrics

### Natural Language Interface
- **Query Capabilities**
  - Spatial queries ("floats in Pacific")
  - Temporal queries ("data from last summer")
  - Parameter queries ("high salinity regions")
  - Combined queries supported

- **Interactive Features**
  - Auto-completion
  - Query suggestions
  - Context-aware help
  - Error correction
- Ask natural language questions about the data
- Example queries:
  - "Show me floats near the equator"
  - "Find high temperature measurements in 2023"
  - "Show salinity data from the Pacific Ocean"
  - "Find floats with deep measurements (>1000m)"

## 🔍 Example Queries

The chatbot supports various query types:

### Region-based Queries
- "Show me floats near the equator"
- "Find data from the Pacific Ocean"
- "Show measurements from tropical regions"

### Parameter-based Queries
- "Find high temperature measurements"
- "Show low salinity data"
- "Find deep measurements"

### Time-based Queries
- "Show data from 2023"
- "Find measurements from March"
- "Show summer data"

### Combined Queries
- "Find high temperature measurements near the equator in 2023"
- "Show salinity data from the Pacific Ocean with deep measurements"

## 🏗️ Architecture

```
NetCDF Files → Data Ingestion → SQLite Database → Query Layer → Visualizations → Chatbot Interface
```

### Data Flow
1. **Ingestion**: NetCDF files are processed and converted to tabular format
2. **Storage**: Data is stored in SQLite with optimized schema and indexes
3. **Querying**: Database supports various filter types (date, location, parameters)
4. **Visualization**: Interactive plots and maps using Plotly and Folium
5. **Chatbot**: Natural language queries are parsed and converted to database queries

## 🔮 Future Enhancements (SIH PoC)

This prototype will be extended with:

### Scalability
- Large dataset ingestion capabilities
- PostgreSQL/MySQL for production scale
- Parallel processing for multiple floats
- Real-time data streaming

### Advanced Analytics
- Machine learning model integration
- Time series forecasting
- Anomaly detection
- Statistical analysis tools

### Enhanced Chatbot
- RAG (Retrieval-Augmented Generation) with vector database
- Large Language Model (LLM) integration
- Advanced NLP for complex queries
- Context-aware conversation handling

### Additional Features
- Multi-user collaboration
- Custom dashboard configurations
- Export capabilities
- API endpoints
- Additional sensor data (oxygen, nitrate, etc.)

## 🧪 Testing

### Test Individual Components

```bash
# Test data ingestion
python data_ingestion.py

# Test database operations
python db_utils.py

# Test visualizations
python visualization.py

# Test chatbot
python chatbot.py
```

### Test Full Pipeline

```bash
# Run the complete application
streamlit run app.py
```

## 📝 Notes

- This is a prototype for demonstration purposes
- Sample data is automatically generated if no NetCDF files are found
- The system is designed to be lightweight and easy to understand
- All components are modular and can be extended independently

## 🤝 Contributing

This is an internal hackathon prototype. For production use, consider:
- Adding comprehensive error handling
- Implementing proper logging
- Adding unit tests
- Optimizing database queries
- Adding data validation

## 📄 License

Internal use only - Hackathon prototype.
