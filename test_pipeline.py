import sys
import traceback
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    try:
        import streamlit
        import pandas as pd
        import plotly.express as px
        import xarray as xr
        import folium
        import streamlit_folium
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_data_ingestion():
    """Test data ingestion module."""
    print("\nTesting data ingestion...")
    try:
        from data_ingestion import ArgoDataIngestion
        
        ingestion = ArgoDataIngestion()
        df = ingestion.ingest_sample_data()
        
        if df.empty:
            print("❌ No data generated")
            return False
        
        print(f"✅ Generated {len(df)} data points from {len(df['float_id'].unique())} floats")
        return True
    except Exception as e:
        print(f"❌ Data ingestion error: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Test database operations."""
    print("\nTesting database operations...")
    try:
        from data_ingestion import ArgoDataIngestion
        from db_utils import ArgoDatabase
        
        # Generate sample data
        ingestion = ArgoDataIngestion()
        df = ingestion.ingest_sample_data()
        
        # Test database operations
        with ArgoDatabase() as db:
            # Insert data
            rows_inserted = db.insert_measurements(df)
            print(f"✅ Inserted {rows_inserted} rows")
            
            # Test queries
            summary = db.get_float_summary()
            print(f"✅ Retrieved summary for {len(summary)} floats")
            
            # Test depth range query
            depth_range_data = db.get_measurements_by_depth_range(0, 100)
            print(f"✅ Depth range query returned {len(depth_range_data)} rows")
            
            # Test parameter query
            temp_data = db.get_measurements_by_parameter('temp', 10, 30)
            print(f"✅ Temperature parameter query returned {len(temp_data)} rows")
        
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        traceback.print_exc()
        return False

def test_visualization():
    """Test visualization module."""
    print("\nTesting visualization...")
    try:
        from data_ingestion import ArgoDataIngestion
        from visualization import ArgoVisualization
        
        # Generate sample data
        ingestion = ArgoDataIngestion()
        df = ingestion.ingest_sample_data()
        
        # Test visualizations
        viz = ArgoVisualization()
        
        # Test profile plot
        float_id = df['float_id'].iloc[0]
        profile_fig = viz.create_profile_plot(df, float_id, 'temp')
        print(f"✅ Created profile plot for float {float_id}")
        
        # Test combined profile plot
        combined_fig = viz.create_combined_profile_plot(df, float_id)
        print(f"✅ Created combined profile plot for float {float_id}")
        
        # Test float map
        float_map = viz.create_float_map(df)
        print(f"✅ Created float map with {len(df['float_id'].unique())} floats")
        
        # Test summary dashboard
        dashboard_fig = viz.create_summary_dashboard(df)
        print("✅ Created summary dashboard")
        
        return True
    except Exception as e:
        print(f"❌ Visualization error: {e}")
        traceback.print_exc()
        return False

def test_chatbot():
    """Test chatbot module."""
    print("\nTesting chatbot...")
    try:
        from data_ingestion import ArgoDataIngestion
        from db_utils import ArgoDatabase
        from chatbot import ArgoChatbot
        
        # Generate sample data and database
        ingestion = ArgoDataIngestion()
        df = ingestion.ingest_sample_data()
        
        with ArgoDatabase() as db:
            db.insert_measurements(df)
            
            chatbot = ArgoChatbot(db)
            
            # Test queries
            test_queries = [
                "Show me floats near the equator",
                "Find high temperature measurements",
                "Show salinity data from the Pacific Ocean"
            ]
            
            for query in test_queries:
                results, explanation, suggestion = chatbot.process_query(query)
                print(f"✅ Query '{query}': {len(results)} results")
        
        return True
    except Exception as e:
        print(f"❌ Chatbot error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 ARGO Float Data Pipeline - Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_data_ingestion,
        test_database,
        test_visualization,
        test_chatbot
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The pipeline is ready to use.")
        print("\n🚀 To run the Streamlit app:")
        print("   streamlit run app.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
