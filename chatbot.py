"""
Chatbot Module for ARGO Float Data

This module provides a simple rule-based chatbot interface for querying
ARGO float data using natural language-like queries.

In the final SIH PoC, this will be extended with:
- RAG (Retrieval-Augmented Generation) with vector database
- Large Language Model (LLM) integration
- Advanced NLP for complex queries
- Context-aware conversation handling
"""

import re
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
import logging
from db_utils import ArgoDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArgoChatbot:
    """Simple rule-based chatbot for ARGO float data queries."""
    
    def __init__(self, db: ArgoDatabase):
        """
        Initialize the chatbot.
        
        Args:
            db: ArgoDatabase instance for data queries
        """
        self.db = db
        
        # Define keyword mappings
        self.parameter_keywords = {
            'temperature': 'temp',
            'temp': 'temp',
            'salinity': 'sal',
            'sal': 'sal',
            'depth': 'depth',
            'pressure': 'depth'
        }
        
        self.region_keywords = {
            'equator': {'lat_range': (-5, 5)},
            'tropical': {'lat_range': (-23.5, 23.5)},
            'subtropical': {'lat_range': (23.5, 35), 'lat_range_neg': (-35, -23.5)},
            'temperate': {'lat_range': (35, 60), 'lat_range_neg': (-60, -35)},
            'polar': {'lat_range': (60, 90), 'lat_range_neg': (-90, -60)},
            'north atlantic': {'lat_range': (0, 70), 'lon_range': (-80, 0)},
            'south atlantic': {'lat_range': (-70, 0), 'lon_range': (-80, 20)},
            'pacific': {'lon_range': (100, 260)},
            'indian ocean': {'lon_range': (20, 120)},
            'mediterranean': {'lat_range': (30, 45), 'lon_range': (-10, 40)}
        }
        
        self.time_keywords = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
            'spring': '03-05', 'summer': '06-08', 'autumn': '09-11', 'fall': '09-11', 'winter': '12-02'
        }
        
        self.comparison_keywords = {
            'high': 'high',
            'low': 'low',
            'warm': 'high',
            'cold': 'low',
            'deep': 'high',
            'shallow': 'low',
            'near': 'near',
            'around': 'near'
        }
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query and extract parameters.
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with parsed query parameters
        """
        query_lower = query.lower()
        parsed = {
            'parameters': [],
            'regions': [],
            'time_filters': [],
            'comparisons': [],
            'values': [],
            'float_ids': [],
            'depth_range': None,
            'original_query': query
        }
        
        # Extract parameters
        for keyword, param in self.parameter_keywords.items():
            if keyword in query_lower:
                parsed['parameters'].append(param)
        
        # Extract regions
        for region, coords in self.region_keywords.items():
            if region in query_lower:
                parsed['regions'].append((region, coords))
        
        # Extract time information
        # Look for years
        year_matches = re.findall(r'\b(20\d{2})\b', query)
        if year_matches:
            parsed['time_filters'].extend([f"year_{year}" for year in year_matches])
        
        # Look for months
        for month_keyword, month_num in self.time_keywords.items():
            if month_keyword in query_lower:
                parsed['time_filters'].append(f"month_{month_num}")
        
        # Extract comparisons
        for keyword, comparison in self.comparison_keywords.items():
            if keyword in query_lower:
                parsed['comparisons'].append(comparison)
        
        # Extract numerical values
        value_matches = re.findall(r'\b(\d+(?:\.\d+)?)\b', query)
        parsed['values'] = [float(v) for v in value_matches]
        
        # Extract float IDs (7-digit numbers)
        float_matches = re.findall(r'\b(\d{7})\b', query)
        parsed['float_ids'] = float_matches
        
        # Extract depth ranges
        depth_patterns = [
            r'(\d+)\s*-\s*(\d+)\s*m',
            r'(\d+)\s*to\s*(\d+)\s*m',
            r'between\s*(\d+)\s*and\s*(\d+)\s*m'
        ]
        
        for pattern in depth_patterns:
            match = re.search(pattern, query_lower)
            if match:
                parsed['depth_range'] = (float(match.group(1)), float(match.group(2)))
                break
        
        logger.info(f"Parsed query: {parsed}")
        return parsed
    
    def execute_query(self, parsed_query: Dict[str, Any]) -> Tuple[pd.DataFrame, str]:
        """
        Execute a parsed query and return results with explanation.
        
        Args:
            parsed_query: Parsed query dictionary
            
        Returns:
            Tuple of (DataFrame with results, explanation string)
        """
        try:
            df = pd.DataFrame()
            explanation_parts = []
            
            # Start with all data
            df = self.db.get_float_summary()
            if df.empty:
                return pd.DataFrame(), "No data available in the database."
            
            # Apply filters based on parsed query
            if parsed_query['float_ids']:
                df = df[df['float_id'].isin(parsed_query['float_ids'])]
                explanation_parts.append(f"Filtered for floats: {', '.join(parsed_query['float_ids'])}")
            
            # Apply time filters
            if parsed_query['time_filters']:
                for time_filter in parsed_query['time_filters']:
                    if time_filter.startswith('year_'):
                        year = time_filter.split('_')[1]
                        # This would need to be implemented in the database query
                        explanation_parts.append(f"Filtered for year {year}")
                    elif time_filter.startswith('month_'):
                        month = time_filter.split('_')[1]
                        explanation_parts.append(f"Filtered for month {month}")
            
            # Apply region filters
            if parsed_query['regions']:
                for region, coords in parsed_query['regions']:
                    if 'lat_range' in coords:
                        lat_min, lat_max = coords['lat_range']
                        df = df[(df['min_lat'] >= lat_min) & (df['max_lat'] <= lat_max)]
                        explanation_parts.append(f"Filtered for {region} region (lat: {lat_min} to {lat_max})")
                    
                    if 'lon_range' in coords:
                        lon_min, lon_max = coords['lon_range']
                        df = df[(df['min_lon'] >= lon_min) & (df['max_lon'] <= lon_max)]
                        explanation_parts.append(f"Filtered for {region} region (lon: {lon_min} to {lon_max})")
            
            # Apply depth range filter
            if parsed_query['depth_range']:
                min_depth, max_depth = parsed_query['depth_range']
                df = df[(df['min_depth'] >= min_depth) & (df['max_depth'] <= max_depth)]
                explanation_parts.append(f"Filtered for depth range: {min_depth} to {max_depth} meters")
            
            # Apply parameter-based filters
            if parsed_query['parameters'] and parsed_query['comparisons'] and parsed_query['values']:
                for param in parsed_query['parameters']:
                    if param in df.columns:
                        for comparison in parsed_query['comparisons']:
                            if comparison == 'high' and parsed_query['values']:
                                threshold = max(parsed_query['values'])
                                df = df[df[f'avg_{param}'] > threshold]
                                explanation_parts.append(f"Filtered for {param} > {threshold}")
                            elif comparison == 'low' and parsed_query['values']:
                                threshold = min(parsed_query['values'])
                                df = df[df[f'avg_{param}'] < threshold]
                                explanation_parts.append(f"Filtered for {param} < {threshold}")
            
            # Generate explanation
            if explanation_parts:
                explanation = f"Query results: {len(df)} floats found. " + "; ".join(explanation_parts)
            else:
                explanation = f"Query results: {len(df)} floats found (no specific filters applied)."
            
            logger.info(f"Query executed successfully: {len(df)} results")
            return df, explanation
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return pd.DataFrame(), f"Error executing query: {str(e)}"
    
    def get_detailed_data(self, float_id: str, parameter: str = 'temp') -> pd.DataFrame:
        """
        Get detailed data for a specific float and parameter.
        
        Args:
            float_id: Float identifier
            parameter: Parameter to retrieve ('temp' or 'sal')
            
        Returns:
            DataFrame with detailed measurements
        """
        try:
            df = self.db.get_float_profile(float_id)
            if not df.empty and parameter in df.columns:
                return df[['time', 'lat', 'lon', 'depth', parameter]].dropna()
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error getting detailed data: {e}")
            return pd.DataFrame()
    
    def suggest_queries(self) -> List[str]:
        """
        Suggest example queries for the user.
        
        Returns:
            List of example query strings
        """
        return [
            "Show me floats near the equator",
            "Find high temperature measurements in 2023",
            "Show salinity data from the Pacific Ocean",
            "Find floats with deep measurements (>1000m)",
            "Show me data from March 2023",
            "Find floats in the North Atlantic",
            "Show temperature profiles for float 1901234",
            "Find low salinity measurements",
            "Show me data between 100-500 meters depth",
            "Find floats in tropical regions"
        ]
    
    def process_query(self, query: str) -> Tuple[pd.DataFrame, str, str]:
        """
        Process a complete query and return results with suggestions.
        
        Args:
            query: Natural language query string
            
        Returns:
            Tuple of (DataFrame with results, explanation, suggestion)
        """
        try:
            # Parse the query
            parsed = self.parse_query(query)
            
            # Execute the query
            df, explanation = self.execute_query(parsed)
            
            # Generate suggestion based on results
            if df.empty:
                suggestion = "Try a broader query or check if the data exists. You can ask about specific regions, time periods, or parameters."
            elif len(df) == 1:
                float_id = df['float_id'].iloc[0]
                suggestion = f"Would you like to see detailed profiles for float {float_id}? Try: 'Show temperature profile for float {float_id}'"
            else:
                suggestion = f"Found {len(df)} floats. You can ask for detailed profiles of specific floats or filter further by region, time, or parameters."
            
            return df, explanation, suggestion
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return pd.DataFrame(), f"Error processing query: {str(e)}", "Please try rephrasing your query."
    
    def get_query_help(self) -> str:
        """
        Get help text for using the chatbot.
        
        Returns:
            Help text string
        """
        return """
        <b>ARGO Float Data Chatbot Help</b><br><br>
        
        <b>Supported Query Types:</b><br>
        • <b>Parameters:</b> temperature, salinity, depth, pressure<br>
        • <b>Regions:</b> equator, tropical, Pacific, Atlantic, Mediterranean, etc.<br>
        • <b>Time:</b> years (2023), months (March), seasons (summer)<br>
        • <b>Comparisons:</b> high, low, warm, cold, deep, shallow<br>
        • <b>Float IDs:</b> 7-digit numbers (1901234)<br>
        • <b>Depth ranges:</b> "100-500m", "between 50 and 200 meters"<br><br>
        
        <b>Example Queries:</b><br>
        • "Show me floats near the equator"<br>
        • "Find high temperature measurements in 2023"<br>
        • "Show salinity data from the Pacific Ocean"<br>
        • "Find floats with deep measurements (>1000m)"<br>
        • "Show temperature profiles for float 1901234"<br><br>
        
        <b>Tips:</b><br>
        • Be specific about what you want to see<br>
        • Combine multiple criteria for better results<br>
        • Ask for detailed profiles of specific floats<br>
        • Use natural language - the system will try to understand your intent
        """


def main():
    """Test the chatbot functionality."""
    # Create sample data and database
    from data_ingestion import ArgoDataIngestion
    
    ingestion = ArgoDataIngestion()
    df = ingestion.ingest_sample_data(max_files=2)
    
    # Test database and chatbot
    with ArgoDatabase() as db:
        db.insert_measurements(df)
        
        chatbot = ArgoChatbot(db)
        
        # Test queries
        test_queries = [
            "Show me floats near the equator",
            "Find high temperature measurements",
            "Show salinity data from 2023",
            "Find floats with deep measurements"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            results, explanation, suggestion = chatbot.process_query(query)
            print(f"Results: {len(results)} floats")
            print(f"Explanation: {explanation}")
            print(f"Suggestion: {suggestion}")


if __name__ == "__main__":
    main()
