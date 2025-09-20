"""
Database Utilities for ARGO Float Data

This module handles SQLite database operations for storing and querying
ARGO float oceanographic data.

In the final SIH PoC, this will be extended with:
- PostgreSQL/MySQL for production scale
- Vector database for similarity search
- Time-series optimized storage
- Real-time data streaming
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime, date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArgoDatabase:
    """Handles SQLite database operations for ARGO float data."""
    
    def __init__(self, db_path: str = "argo_data.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # Create main data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS argo_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    float_id TEXT NOT NULL,
                    time TIMESTAMP NOT NULL,
                    lat REAL NOT NULL,
                    lon REAL NOT NULL,
                    depth REAL NOT NULL,
                    temp REAL,
                    sal REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create float metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS float_metadata (
                    float_id TEXT PRIMARY KEY,
                    provider TEXT,
                    platform_number TEXT,
                    wmo_type TEXT,
                    first_measurement TIMESTAMP,
                    last_measurement TIMESTAMP,
                    total_measurements INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_float_time 
                ON argo_measurements(float_id, time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_location 
                ON argo_measurements(lat, lon)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_depth 
                ON argo_measurements(depth)
            """)
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def insert_measurements(self, df: pd.DataFrame) -> int:
        """
        Insert oceanographic measurements into the database.
        
        Args:
            df: DataFrame with oceanographic data
            
        Returns:
            Number of rows inserted
        """
        try:
            if df.empty:
                logger.warning("Empty DataFrame provided")
                return 0
            
            # Prepare data for insertion
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    row['float_id'],
                    row['time'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(row['time']) else None,
                    row['lat'],
                    row['lon'],
                    row['depth'],
                    row['temp'],
                    row['sal']
                ))
            
            cursor = self.connection.cursor()
            cursor.executemany("""
                INSERT INTO argo_measurements 
                (float_id, time, lat, lon, depth, temp, sal)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            self.connection.commit()
            rows_inserted = cursor.rowcount
            logger.info(f"Inserted {rows_inserted} measurements into database")
            
            # Update float metadata
            self._update_float_metadata(df)
            
            return rows_inserted
            
        except Exception as e:
            logger.error(f"Error inserting measurements: {e}")
            self.connection.rollback()
            raise
    
    def _update_float_metadata(self, df: pd.DataFrame):
        """Update float metadata table with summary statistics."""
        try:
            cursor = self.connection.cursor()
            
            for float_id in df['float_id'].unique():
                float_data = df[df['float_id'] == float_id]
                
                first_time = float_data['time'].min()
                last_time = float_data['time'].max()
                total_measurements = len(float_data)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO float_metadata 
                    (float_id, first_measurement, last_measurement, total_measurements)
                    VALUES (?, ?, ?, ?)
                """, (float_id, 
                      first_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(first_time) else None,
                      last_time.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(last_time) else None,
                      total_measurements))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating float metadata: {e}")
    
    def get_profiles_by_date_range(self, start_date: str, end_date: str, 
                                 float_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get profiles within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            float_ids: Optional list of float IDs to filter by
            
        Returns:
            DataFrame with filtered measurements
        """
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE time BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            
            if float_ids:
                placeholders = ','.join(['?' for _ in float_ids])
                query += f" AND float_id IN ({placeholders})"
                params.extend(float_ids)
            
            query += " ORDER BY float_id, time, depth"
            
            df = pd.read_sql_query(query, self.connection, params=params)
            logger.info(f"Retrieved {len(df)} measurements for date range {start_date} to {end_date}")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by date range: {e}")
            return pd.DataFrame()
    
    def get_profiles_by_bbox(self, min_lat: float, max_lat: float, 
                           min_lon: float, max_lon: float) -> pd.DataFrame:
        """
        Get profiles within a bounding box.
        
        Args:
            min_lat: Minimum latitude
            max_lat: Maximum latitude
            min_lon: Minimum longitude
            max_lon: Maximum longitude
            
        Returns:
            DataFrame with filtered measurements
        """
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE lat BETWEEN ? AND ? 
                AND lon BETWEEN ? AND ?
                ORDER BY float_id, time, depth
            """
            
            df = pd.read_sql_query(query, self.connection, 
                                 params=[min_lat, max_lat, min_lon, max_lon])
            logger.info(f"Retrieved {len(df)} measurements in bounding box")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by bounding box: {e}")
            return pd.DataFrame()
    
    def get_nearest_float(self, lat: float, lon: float, 
                         max_distance_km: float = 1000) -> Optional[Dict]:
        """
        Find the nearest float to a given point.
        
        Args:
            lat: Target latitude
            lon: Target longitude
            max_distance_km: Maximum distance in kilometers
            
        Returns:
            Dictionary with nearest float information or None
        """
        try:
            # Get unique float positions (latest measurement for each float)
            query = """
                SELECT float_id, lat, lon, time,
                       ((lat - ?) * (lat - ?) + (lon - ?) * (lon - ?)) as distance_sq
                FROM argo_measurements a1
                WHERE time = (
                    SELECT MAX(time) 
                    FROM argo_measurements a2 
                    WHERE a2.float_id = a1.float_id
                )
                ORDER BY distance_sq
                LIMIT 1
            """
            
            cursor = self.connection.cursor()
            cursor.execute(query, (lat, lat, lon, lon))
            result = cursor.fetchone()
            
            if result:
                float_id, float_lat, float_lon, time, distance_sq = result
                distance_km = (distance_sq ** 0.5) * 111  # Rough conversion to km
                
                if distance_km <= max_distance_km:
                    return {
                        'float_id': float_id,
                        'lat': float_lat,
                        'lon': float_lon,
                        'time': time,
                        'distance_km': distance_km
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding nearest float: {e}")
            return None
    
    def get_float_profile(self, float_id: str, 
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get a complete profile for a specific float.
        
        Args:
            float_id: Float identifier
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            DataFrame with float profile data
        """
        try:
            query = "SELECT * FROM argo_measurements WHERE float_id = ?"
            params = [float_id]
            
            if start_date:
                query += " AND time >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND time <= ?"
                params.append(end_date)
            
            query += " ORDER BY time, depth"
            
            df = pd.read_sql_query(query, self.connection, params=params)
            logger.info(f"Retrieved {len(df)} measurements for float {float_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving float profile: {e}")
            return pd.DataFrame()
    
    def get_float_summary(self) -> pd.DataFrame:
        """
        Get summary statistics for all floats.
        
        Returns:
            DataFrame with float summary information
        """
        try:
            query = """
                SELECT 
                    float_id,
                    COUNT(*) as total_measurements,
                    MIN(time) as first_measurement,
                    MAX(time) as last_measurement,
                    MIN(lat) as min_lat,
                    MAX(lat) as max_lat,
                    MIN(lon) as min_lon,
                    MAX(lon) as max_lon,
                    MIN(depth) as min_depth,
                    MAX(depth) as max_depth,
                    AVG(temp) as avg_temp,
                    AVG(sal) as avg_sal
                FROM argo_measurements
                GROUP BY float_id
                ORDER BY float_id
            """
            
            df = pd.read_sql_query(query, self.connection)
            logger.info(f"Retrieved summary for {len(df)} floats")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving float summary: {e}")
            return pd.DataFrame()
    
    def get_measurements_by_depth_range(self, min_depth: float, max_depth: float) -> pd.DataFrame:
        """
        Get measurements within a specific depth range.
        
        Args:
            min_depth: Minimum depth in meters
            max_depth: Maximum depth in meters
            
        Returns:
            DataFrame with filtered measurements
        """
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE depth BETWEEN ? AND ?
                ORDER BY float_id, time, depth
            """
            
            df = pd.read_sql_query(query, self.connection, params=[min_depth, max_depth])
            logger.info(f"Retrieved {len(df)} measurements in depth range {min_depth}-{max_depth}m")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by depth range: {e}")
            return pd.DataFrame()
    
    def get_measurements_by_parameter(self, parameter: str, 
                                    min_value: float, max_value: float) -> pd.DataFrame:
        """
        Get measurements within a parameter value range.
        
        Args:
            parameter: Parameter name ('temp' or 'sal')
            min_value: Minimum parameter value
            max_value: Maximum parameter value
            
        Returns:
            DataFrame with filtered measurements
        """
        try:
            if parameter not in ['temp', 'sal']:
                raise ValueError("Parameter must be 'temp' or 'sal'")
            
            query = f"""
                SELECT * FROM argo_measurements 
                WHERE {parameter} BETWEEN ? AND ?
                ORDER BY float_id, time, depth
            """
            
            df = pd.read_sql_query(query, self.connection, params=[min_value, max_value])
            logger.info(f"Retrieved {len(df)} measurements with {parameter} in range {min_value}-{max_value}")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by parameter: {e}")
            return pd.DataFrame()
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Test the database functionality."""
    # Create sample data
    from data_ingestion import ArgoDataIngestion
    
    ingestion = ArgoDataIngestion()
    df = ingestion.ingest_sample_data(max_files=2)
    
    # Test database operations
    with ArgoDatabase() as db:
        # Insert data
        rows_inserted = db.insert_measurements(df)
        print(f"Inserted {rows_inserted} rows")
        
        # Test queries
        summary = db.get_float_summary()
        print(f"Float summary:\n{summary}")
        
        # Test date range query
        date_range_data = db.get_profiles_by_date_range('2023-01-01', '2023-12-31')
        print(f"Date range query returned {len(date_range_data)} rows")
        
        # Test nearest float
        nearest = db.get_nearest_float(0, 0)
        if nearest:
            print(f"Nearest float: {nearest}")


if __name__ == "__main__":
    main()
