# ARGO Float Data Pipeline - Hackathon Prototype

A lightweight prototype demonstrating an end-to-end pipeline for ARGO oceanographic float data analysis.

## 🌊 Overview

This prototype showcases a complete data pipeline from NetCDF file ingestion to interactive visualizations and natural language querying. Built for internal hackathon demonstration.

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

### 3. Interactive Visualizations
- Profile plots (Temperature vs Depth, Salinity vs Depth)
- Interactive maps with float locations
- Time series analysis
- Depth-time heatmaps
- Combined profile visualizations

### 4. Natural Language Chatbot
- Rule-based query processing
- Support for region, time, and parameter filters
- Example query suggestions
- Contextual help system

## 🛠️ Tech Stack

- **Python 3.8+**
- **Streamlit** - Web application framework
- **xarray/netCDF4** - NetCDF file processing
- **pandas** - Data manipulation
- **SQLite3** - Database storage
- **Plotly** - Interactive visualizations
- **Folium** - Map visualizations

## 📁 Project Structure

```
project/
├── app.py                 # Main Streamlit application
├── data_ingestion.py      # NetCDF data processing
├── db_utils.py           # Database operations
├── visualization.py      # Plot and map generation
├── chatbot.py            # Natural language query processing
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

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

## 📊 Usage

### Loading Data
1. Click "Load Sample Data" in the sidebar
2. The system will automatically generate sample ARGO float data
3. Data is stored in SQLite database for querying

### Interactive Map Tab
- View float locations on an interactive map
- Click on floats to see detailed information
- Filter by surface data or view all measurements
- Select specific floats for detailed analysis

### Profile Plots Tab
- Choose from different plot types:
  - Temperature Profile
  - Salinity Profile
  - Combined Profile
  - Time Series
  - Depth Heatmap
- Select specific floats and parameters
- View summary statistics

### Chatbot Query Tab
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
