
# """
# Database Utilities for ARGO Float Data - Fixed Version (No Infinite Loops)

# This module handles SQLite database operations for storing and querying
# ARGO float oceanographic data with strict validation and no time dependency.

# Key fixes:
# - Fixed infinite loop in batch processing
# - Improved memory management for large datasets
# - Added batch size limits and timeouts
# - Better error handling and progress tracking
# """

# import sqlite3
# import pandas as pd
# import numpy as np
# from pathlib import Path
# from typing import List, Dict, Optional, Tuple, Any
# import logging
# from datetime import datetime
# import time

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# class ArgoDatabase:
#     """Handles SQLite database operations for ARGO float data with strict validation."""
    
#     def __init__(self, db_path: str = "argo_data.db"):
#         """
#         Initialize the database connection.
        
#         Args:
#             db_path: Path to the SQLite database file
#         """
#         self.db_path = Path(db_path)
#         self.connection = None
#         self._create_tables()
    
#     def _create_tables(self):
#         """Create database tables with proper schema (no time column)."""
#         try:
#             # Check if database exists and has incompatible schema
#             if self.db_path.exists():
#                 self.connection = sqlite3.connect(self.db_path)
#                 cursor = self.connection.cursor()
                
#                 # Check if old schema exists (with time column)
#                 try:
#                     cursor.execute("PRAGMA table_info(argo_measurements)")
#                     columns = [row[1] for row in cursor.fetchall()]
                    
#                     if 'time' in columns:
#                         logger.info("Found incompatible database schema - recreating database")
#                         self.connection.close()
#                         self.db_path.unlink()  # Delete old database
#                     else:
#                         # Schema is compatible, just return
#                         logger.info("Database schema is compatible")
#                         return
#                 except sqlite3.OperationalError:
#                     # Table doesn't exist yet, continue with creation
#                     pass
            
#             # Create fresh connection
#             self.connection = sqlite3.connect(self.db_path)
#             cursor = self.connection.cursor()
            
#             # Enable foreign key constraints
#             cursor.execute("PRAGMA foreign_keys = ON")
            
#             # Create main measurements table (NO TIME COLUMN)
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS argo_measurements (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     float_id TEXT NOT NULL,
#                     lat REAL NOT NULL CHECK(lat >= -90 AND lat <= 90),
#                     lon REAL NOT NULL CHECK(lon >= -180 AND lon <= 180),
#                     depth REAL NOT NULL CHECK(depth >= 0),
#                     temp REAL CHECK(temp IS NULL OR (temp >= -5 AND temp <= 50)),
#                     sal REAL CHECK(sal IS NULL OR (sal >= 0 AND sal <= 50)),
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             # Create float metadata table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS float_metadata (
#                     float_id TEXT PRIMARY KEY,
#                     provider TEXT,
#                     total_measurements INTEGER DEFAULT 0,
#                     min_depth REAL,
#                     max_depth REAL,
#                     avg_depth REAL,
#                     min_lat REAL,
#                     max_lat REAL,
#                     min_lon REAL,
#                     max_lon REAL,
#                     avg_temp REAL,
#                     avg_sal REAL,
#                     temp_measurements INTEGER DEFAULT 0,
#                     sal_measurements INTEGER DEFAULT 0,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             # Create data quality table
#             cursor.execute("""
#                 CREATE TABLE IF NOT EXISTS data_quality_log (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     float_id TEXT NOT NULL,
#                     file_name TEXT,
#                     total_records INTEGER,
#                     valid_records INTEGER,
#                     invalid_coords INTEGER DEFAULT 0,
#                     invalid_depth INTEGER DEFAULT 0,
#                     processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
            
#             # Create performance indexes
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_float_id ON argo_measurements(float_id)")
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_location ON argo_measurements(lat, lon)")
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_depth ON argo_measurements(depth)")
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_temp ON argo_measurements(temp) WHERE temp IS NOT NULL")
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_sal ON argo_measurements(sal) WHERE sal IS NOT NULL")
#             cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_composite ON argo_measurements(float_id, depth)")
            
#             self.connection.commit()
#             logger.info("Database tables and indexes created successfully")
            
#         except Exception as e:
#             logger.error(f"Error creating database tables: {e}")
#             raise
    
#     def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
#         """
#         Validate DataFrame before insertion and return clean data + validation report.
#         FIXED: Added memory management and processing limits.
        
#         Args:
#             df: Input DataFrame
            
#         Returns:
#             Tuple of (clean_df, validation_report)
#         """
#         if df.empty:
#             return df, {"error": "Empty DataFrame"}
        
#         original_count = len(df)
        
#         # SAFETY CHECK: Limit processing size to prevent memory issues
#         MAX_ROWS = 1000000  # Process max 1M rows at a time
#         if original_count > MAX_ROWS:
#             logger.warning(f"DataFrame has {original_count} rows, limiting to {MAX_ROWS} for processing")
#             df = df.head(MAX_ROWS)
#             original_count = len(df)
        
#         validation_report = {
#             "original_records": original_count,
#             "issues_found": []
#         }
        
#         # Check required columns
#         required_columns = ['float_id', 'lat', 'lon', 'depth']
#         missing_columns = [col for col in required_columns if col not in df.columns]
#         if missing_columns:
#             validation_report["issues_found"].append(f"Missing required columns: {missing_columns}")
#             return pd.DataFrame(), validation_report
        
#         # Start with original data
#         clean_df = df.copy()
        
#         # Remove records with NULL essential fields
#         before_null_check = len(clean_df)
#         clean_df = clean_df.dropna(subset=['float_id', 'lat', 'lon', 'depth'])
#         null_removed = before_null_check - len(clean_df)
#         if null_removed > 0:
#             validation_report["issues_found"].append(f"Removed {null_removed} records with NULL essential fields")
        
#         # Validate coordinates
#         before_coord_check = len(clean_df)
#         clean_df = clean_df[
#             (clean_df['lat'] >= -90) & (clean_df['lat'] <= 90) &
#             (clean_df['lon'] >= -180) & (clean_df['lon'] <= 180)
#         ]
#         coord_removed = before_coord_check - len(clean_df)
#         if coord_removed > 0:
#             validation_report["issues_found"].append(f"Removed {coord_removed} records with invalid coordinates")
        
#         # Validate depth
#         before_depth_check = len(clean_df)
#         clean_df = clean_df[(clean_df['depth'] >= 0) & (clean_df['depth'] <= 12000)]
#         depth_removed = before_depth_check - len(clean_df)
#         if depth_removed > 0:
#             validation_report["issues_found"].append(f"Removed {depth_removed} records with invalid depth")
        
#         # Validate temperature (if present)
#         if 'temp' in clean_df.columns:
#             before_temp_check = len(clean_df)
#             # Remove records with invalid temperature (keep NULL)
#             clean_df = clean_df[
#                 (clean_df['temp'].isnull()) | 
#                 ((clean_df['temp'] >= -5) & (clean_df['temp'] <= 50))
#             ]
#             temp_removed = before_temp_check - len(clean_df)
#             if temp_removed > 0:
#                 validation_report["issues_found"].append(f"Removed {temp_removed} records with invalid temperature")
        
#         # Validate salinity (if present)
#         if 'sal' in clean_df.columns:
#             before_sal_check = len(clean_df)
#             # Remove records with invalid salinity (keep NULL)
#             clean_df = clean_df[
#                 (clean_df['sal'].isnull()) | 
#                 ((clean_df['sal'] >= 0) & (clean_df['sal'] <= 50))
#             ]
#             sal_removed = before_sal_check - len(clean_df)
#             if sal_removed > 0:
#                 validation_report["issues_found"].append(f"Removed {sal_removed} records with invalid salinity")
        
#         # Clean float_id (ensure it's string and not empty)
#         clean_df['float_id'] = clean_df['float_id'].astype(str)
#         before_float_check = len(clean_df)
#         clean_df = clean_df[clean_df['float_id'].str.strip() != '']
#         float_removed = before_float_check - len(clean_df)
#         if float_removed > 0:
#             validation_report["issues_found"].append(f"Removed {float_removed} records with empty float_id")
        
#         validation_report.update({
#             "final_records": len(clean_df),
#             "records_removed": original_count - len(clean_df),
#             "success_rate": (len(clean_df) / original_count * 100) if original_count > 0 else 0
#         })
        
#         return clean_df, validation_report
    
#     def insert_measurements(self, df: pd.DataFrame, batch_size: int = 5000) -> int:
#         """
#         FIXED: Insert measurements with proper batch processing and timeout protection.
        
#         Args:
#             df: DataFrame with oceanographic data
#             batch_size: Number of records to insert per batch (reduced from 10000)
            
#         Returns:
#             Number of rows successfully inserted
#         """
#         try:
#             if df.empty:
#                 logger.warning("Empty DataFrame provided")
#                 return 0
            
#             start_time = time.time()
#             MAX_PROCESSING_TIME = 3600  # 1 hour timeout
            
#             # Validate data first
#             clean_df, validation_report = self.validate_dataframe(df)
            
#             # Log validation results
#             logger.info(f"Data validation: {validation_report['original_records']} -> {validation_report['final_records']} records")
#             if validation_report['issues_found']:
#                 for issue in validation_report['issues_found'][:5]:  # Limit log output
#                     logger.warning(f"  {issue}")
            
#             if clean_df.empty:
#                 logger.error("No valid records to insert after validation")
#                 return 0
            
#             # SAFETY: Further limit for very large datasets
#             if len(clean_df) > 500000:  # 500k record limit per call
#                 logger.warning(f"Dataset too large ({len(clean_df)} records), processing first 500k only")
#                 clean_df = clean_df.head(500000)
            
#             # Prepare data for batch insertion
#             cursor = self.connection.cursor()
#             total_inserted = 0
#             batch_count = 0
            
#             # FIXED: Proper batch processing with safety checks
#             total_batches = (len(clean_df) + batch_size - 1) // batch_size
#             logger.info(f"Processing {len(clean_df)} records in {total_batches} batches of {batch_size}")
            
#             for batch_start in range(0, len(clean_df), batch_size):
#                 # SAFETY: Check processing time
#                 if time.time() - start_time > MAX_PROCESSING_TIME:
#                     logger.error("Processing timeout reached, stopping insertion")
#                     break
                
#                 batch_end = min(batch_start + batch_size, len(clean_df))
#                 batch_df = clean_df.iloc[batch_start:batch_end]
#                 batch_count += 1
                
#                 # Log progress every 10 batches
#                 if batch_count % 10 == 0:
#                     elapsed = time.time() - start_time
#                     logger.info(f"Processing batch {batch_count}/{total_batches} ({total_inserted:,} inserted so far, {elapsed:.1f}s elapsed)")
                
#                 batch_data = []
                
#                 # FIXED: Iterate properly through batch
#                 for idx in range(len(batch_df)):
#                     try:
#                         row = batch_df.iloc[idx]
#                         batch_data.append((
#                             str(row['float_id']).strip(),
#                             float(row['lat']),
#                             float(row['lon']),
#                             float(row['depth']),
#                             float(row['temp']) if pd.notna(row['temp']) else None,
#                             float(row['sal']) if pd.notna(row['sal']) else None
#                         ))
#                     except Exception as e:
#                         logger.warning(f"Error processing row {idx} in batch {batch_count}: {e}")
#                         continue
                
#                 # SAFETY: Check if we have data to insert
#                 if not batch_data:
#                     logger.warning(f"No valid data in batch {batch_count}")
#                     continue
                
#                 try:
#                     # Insert batch with timeout protection
#                     cursor.executemany("""
#                         INSERT INTO argo_measurements 
#                         (float_id, lat, lon, depth, temp, sal)
#                         VALUES (?, ?, ?, ?, ?, ?)
#                     """, batch_data)
                    
#                     batch_inserted = len(batch_data)
#                     total_inserted += batch_inserted
                    
#                     # Commit every 10 batches to prevent excessive memory usage
#                     if batch_count % 10 == 0:
#                         self.connection.commit()
#                         logger.info(f"Committed {total_inserted:,} records so far")
                    
#                 except Exception as e:
#                     logger.error(f"Error inserting batch {batch_count}: {e}")
#                     self.connection.rollback()
#                     continue
                
#                 # SAFETY: Check if we're processing too slowly
#                 if batch_count > 100 and (time.time() - start_time) / batch_count > 10:  # More than 10s per batch
#                     logger.warning("Processing too slow, may need to reduce batch size or optimize data")
            
#             # Final commit
#             self.connection.commit()
            
#             elapsed_time = time.time() - start_time
#             logger.info(f"Successfully inserted {total_inserted:,} measurements in {elapsed_time:.1f}s ({total_inserted/elapsed_time:.1f} records/sec)")
            
#             # Update metadata in smaller chunks to prevent memory issues
#             if total_inserted > 0:
#                 try:
#                     self._update_float_metadata_chunked(clean_df.head(total_inserted))
#                     self._log_data_quality(clean_df.head(total_inserted), validation_report)
#                 except Exception as e:
#                     logger.warning(f"Error updating metadata: {e}")
            
#             return total_inserted
            
#         except Exception as e:
#             logger.error(f"Error inserting measurements: {e}")
#             if self.connection:
#                 self.connection.rollback()
#             raise
    
#     def _update_float_metadata_chunked(self, df: pd.DataFrame):
#         """FIXED: Update float metadata with chunking for large datasets."""
#         try:
#             cursor = self.connection.cursor()
#             unique_floats = df['float_id'].unique()
            
#             logger.info(f"Updating metadata for {len(unique_floats)} floats")
            
#             # Process floats in chunks to avoid memory issues
#             FLOAT_CHUNK_SIZE = 50
#             for i in range(0, len(unique_floats), FLOAT_CHUNK_SIZE):
#                 float_chunk = unique_floats[i:i+FLOAT_CHUNK_SIZE]
                
#                 for float_id in float_chunk:
#                     try:
#                         float_data = df[df['float_id'] == float_id]
                        
#                         if len(float_data) == 0:
#                             continue
                        
#                         # Calculate statistics
#                         stats = {
#                             'total_measurements': len(float_data),
#                             'min_depth': float_data['depth'].min(),
#                             'max_depth': float_data['depth'].max(),
#                             'avg_depth': float_data['depth'].mean(),
#                             'min_lat': float_data['lat'].min(),
#                             'max_lat': float_data['lat'].max(),
#                             'min_lon': float_data['lon'].min(),
#                             'max_lon': float_data['lon'].max(),
#                             'temp_measurements': float_data['temp'].notna().sum(),
#                             'sal_measurements': float_data['sal'].notna().sum(),
#                             'avg_temp': float_data['temp'].mean() if float_data['temp'].notna().any() else None,
#                             'avg_sal': float_data['sal'].mean() if float_data['sal'].notna().any() else None
#                         }
                        
#                         cursor.execute("""
#                             INSERT OR REPLACE INTO float_metadata 
#                             (float_id, total_measurements, min_depth, max_depth, avg_depth,
#                              min_lat, max_lat, min_lon, max_lon, avg_temp, avg_sal,
#                              temp_measurements, sal_measurements, updated_at)
#                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
#                         """, (
#                             str(float_id),
#                             stats['total_measurements'],
#                             stats['min_depth'],
#                             stats['max_depth'],
#                             stats['avg_depth'],
#                             stats['min_lat'],
#                             stats['max_lat'],
#                             stats['min_lon'],
#                             stats['max_lon'],
#                             stats['avg_temp'],
#                             stats['avg_sal'],
#                             stats['temp_measurements'],
#                             stats['sal_measurements']
#                         ))
#                     except Exception as e:
#                         logger.warning(f"Error updating metadata for float {float_id}: {e}")
                
#                 # Commit after each chunk
#                 self.connection.commit()
            
#             logger.info(f"Updated metadata for {len(unique_floats)} floats")
            
#         except Exception as e:
#             logger.error(f"Error updating float metadata: {e}")
    
#     def _log_data_quality(self, df: pd.DataFrame, validation_report: Dict):
#         """Log data quality metrics for monitoring."""
#         try:
#             cursor = self.connection.cursor()
#             unique_floats = df['float_id'].unique()
            
#             # Process in smaller chunks
#             for float_id in unique_floats[:100]:  # Limit to first 100 floats for logging
#                 try:
#                     float_data = df[df['float_id'] == float_id]
                    
#                     cursor.execute("""
#                         INSERT INTO data_quality_log
#                         (float_id, total_records, valid_records)
#                         VALUES (?, ?, ?)
#                     """, (
#                         str(float_id),
#                         validation_report.get('original_records', 0),
#                         len(float_data)
#                     ))
#                 except Exception as e:
#                     logger.warning(f"Error logging quality for float {float_id}: {e}")
            
#             self.connection.commit()
            
#         except Exception as e:
#             logger.error(f"Error logging data quality: {e}")
    
#     def get_measurements_by_bbox(self, min_lat: float, max_lat: float, 
#                                min_lon: float, max_lon: float, 
#                                limit: int = None) -> pd.DataFrame:
#         """Get measurements within a bounding box."""
#         try:
#             query = """
#                 SELECT * FROM argo_measurements 
#                 WHERE lat BETWEEN ? AND ? 
#                 AND lon BETWEEN ? AND ?
#                 ORDER BY float_id, depth
#             """
#             params = [min_lat, max_lat, min_lon, max_lon]
            
#             if limit:
#                 query += " LIMIT ?"
#                 params.append(limit)
            
#             df = pd.read_sql_query(query, self.connection, params=params)
#             logger.info(f"Retrieved {len(df)} measurements in bounding box")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error querying by bounding box: {e}")
#             return pd.DataFrame()
    
#     def get_measurements_by_depth_range(self, min_depth: float, max_depth: float,
#                                       limit: int = None) -> pd.DataFrame:
#         """Get measurements within a depth range."""
#         try:
#             query = """
#                 SELECT * FROM argo_measurements 
#                 WHERE depth BETWEEN ? AND ?
#                 ORDER BY float_id, depth
#             """
#             params = [min_depth, max_depth]
            
#             if limit:
#                 query += " LIMIT ?"
#                 params.append(limit)
            
#             df = pd.read_sql_query(query, self.connection, params=params)
#             logger.info(f"Retrieved {len(df)} measurements in depth range {min_depth}-{max_depth}m")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error querying by depth range: {e}")
#             return pd.DataFrame()
    
#     def get_measurements_by_parameter(self, parameter: str, min_value: float, max_value: float,
#                                     limit: int = None) -> pd.DataFrame:
#         """Get measurements within a parameter value range."""
#         try:
#             if parameter not in ['temp', 'sal']:
#                 raise ValueError("Parameter must be 'temp' or 'sal'")
            
#             query = f"""
#                 SELECT * FROM argo_measurements 
#                 WHERE {parameter} BETWEEN ? AND ?
#                 AND {parameter} IS NOT NULL
#                 ORDER BY float_id, depth
#             """
#             params = [min_value, max_value]
            
#             if limit:
#                 query += " LIMIT ?"
#                 params.append(limit)
            
#             df = pd.read_sql_query(query, self.connection, params=params)
#             logger.info(f"Retrieved {len(df)} measurements with {parameter} in range {min_value}-{max_value}")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error querying by parameter: {e}")
#             return pd.DataFrame()
    
#     def get_float_profile(self, float_id: str) -> pd.DataFrame:
#         """Get complete profile for a specific float."""
#         try:
#             query = """
#                 SELECT * FROM argo_measurements 
#                 WHERE float_id = ?
#                 ORDER BY depth
#             """
            
#             df = pd.read_sql_query(query, self.connection, params=[str(float_id)])
#             logger.info(f"Retrieved {len(df)} measurements for float {float_id}")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error retrieving float profile: {e}")
#             return pd.DataFrame()
    
#     def get_float_summary(self) -> pd.DataFrame:
#         """Get comprehensive summary for all floats."""
#         try:
#             query = """
#                 SELECT 
#                     m.float_id,
#                     COUNT(*) as total_measurements,
#                     MIN(m.lat) as min_lat,
#                     MAX(m.lat) as max_lat,
#                     MIN(m.lon) as min_lon,
#                     MAX(m.lon) as max_lon,
#                     MIN(m.depth) as min_depth,
#                     MAX(m.depth) as max_depth,
#                     AVG(m.depth) as avg_depth,
#                     COUNT(CASE WHEN m.temp IS NOT NULL THEN 1 END) as temp_count,
#                     COUNT(CASE WHEN m.sal IS NOT NULL THEN 1 END) as sal_count,
#                     AVG(m.temp) as avg_temp,
#                     AVG(m.sal) as avg_sal,
#                     MIN(m.temp) as min_temp,
#                     MAX(m.temp) as max_temp,
#                     MIN(m.sal) as min_sal,
#                     MAX(m.sal) as max_sal
#                 FROM argo_measurements m
#                 GROUP BY m.float_id
#                 ORDER BY m.float_id
#             """
            
#             df = pd.read_sql_query(query, self.connection)
#             logger.info(f"Retrieved summary for {len(df)} floats")
#             return df
            
#         except Exception as e:
#             logger.error(f"Error retrieving float summary: {e}")
#             return pd.DataFrame()
    
#     def get_database_stats(self) -> Dict:
#         """Get comprehensive database statistics."""
#         try:
#             cursor = self.connection.cursor()
            
#             # Basic counts
#             cursor.execute("SELECT COUNT(*) FROM argo_measurements")
#             total_measurements = cursor.fetchone()[0]
            
#             cursor.execute("SELECT COUNT(DISTINCT float_id) FROM argo_measurements")
#             unique_floats = cursor.fetchone()[0]
            
#             # Data completeness
#             cursor.execute("""
#                 SELECT 
#                     COUNT(CASE WHEN temp IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as temp_completeness,
#                     COUNT(CASE WHEN sal IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as sal_completeness,
#                     COUNT(CASE WHEN temp IS NOT NULL AND sal IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as both_complete
#                 FROM argo_measurements
#             """)
#             temp_comp, sal_comp, both_comp = cursor.fetchone()
            
#             # Geographic coverage
#             cursor.execute("""
#                 SELECT MIN(lat), MAX(lat), MIN(lon), MAX(lon),
#                        MIN(depth), MAX(depth), AVG(depth)
#                 FROM argo_measurements
#             """)
#             min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, avg_depth = cursor.fetchone()
            
#             # Parameter ranges
#             cursor.execute("""
#                 SELECT MIN(temp), MAX(temp), AVG(temp),
#                        MIN(sal), MAX(sal), AVG(sal)
#                 FROM argo_measurements
#                 WHERE temp IS NOT NULL AND sal IS NOT NULL
#             """)
#             temp_stats = cursor.fetchone()
            
#             # Database file size
#             db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            
#             return {
#                 "database_file": str(self.db_path),
#                 "database_size_mb": round(db_size_mb, 2),
#                 "total_measurements": total_measurements,
#                 "unique_floats": unique_floats,
#                 "avg_measurements_per_float": round(total_measurements / unique_floats, 1) if unique_floats > 0 else 0,
#                 "data_completeness": {
#                     "temperature": round(temp_comp, 2),
#                     "salinity": round(sal_comp, 2),
#                     "both_parameters": round(both_comp, 2)
#                 },
#                 "geographic_coverage": {
#                     "latitude_range": [round(min_lat, 3), round(max_lat, 3)],
#                     "longitude_range": [round(min_lon, 3), round(max_lon, 3)],
#                 },
#                 "depth_statistics": {
#                     "range": [round(min_depth, 1), round(max_depth, 1)],
#                     "average": round(avg_depth, 1)
#                 },
#                 "parameter_ranges": {
#                     "temperature": [round(temp_stats[0], 2), round(temp_stats[1], 2)] if temp_stats[0] else None,
#                     "salinity": [round(temp_stats[3], 2), round(temp_stats[4], 2)] if temp_stats[3] else None
#                 } if temp_stats else None
#             }
            
#         except Exception as e:
#             logger.error(f"Error generating database statistics: {e}")
#             return {"error": str(e)}
    
#     def optimize_database(self):
#         """Optimize database performance."""
#         try:
#             cursor = self.connection.cursor()
            
#             logger.info("Optimizing database...")
            
#             # Update table statistics
#             cursor.execute("ANALYZE")
            
#             # Vacuum database to reclaim space
#             cursor.execute("VACUUM")
            
#             self.connection.commit()
#             logger.info("Database optimization completed")
            
#         except Exception as e:
#             logger.error(f"Error optimizing database: {e}")
    
#     def close(self):
#         """Close database connection."""
#         if self.connection:
#             self.connection.close()
#             logger.info("Database connection closed")
    
#     def __enter__(self):
#         """Context manager entry."""
#         return self
    
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         """Context manager exit."""
#         self.close()


# def main():
#     """Test database functionality with small sample to prevent infinite loops."""
#     try:
#         logger.info("Testing database operations with LIMITED sample...")
        
#         # Create minimal test data
#         test_data = pd.DataFrame({
#             'float_id': ['1234567'] * 100 + ['2345678'] * 100,  # Only 200 records for testing
#             'lat': [45.0 + i*0.01 for i in range(200)],
#             'lon': [-120.0 + i*0.01 for i in range(200)],
#             'depth': [i*2 for i in range(200)],
#             'temp': [15.5 - i*0.01 for i in range(200)],
#             'sal': [35.0 + np.random.random(200) * 0.5]
#         })
        
#         with ArgoDatabase("test_argo.db") as db:
#             logger.info("Starting test insertion...")
#             inserted = db.insert_measurements(test_data, batch_size=50)
#             print(f"Inserted {inserted} test records")
            
#             # Test queries
#             summary = db.get_float_summary()
#             print(f"Float summary: {len(summary)} floats found")
            
#             stats = db.get_database_stats()
#             print(f"Database stats: {stats.get('total_measurements', 0)} total measurements")
            
#             # Clean up test database
#             db.close()
#             test_db_path = Path("test_argo.db")
#             if test_db_path.exists():
#                 test_db_path.unlink()
#                 logger.info("Cleaned up test database")
        
#         logger.info("Database testing completed successfully")
        
#     except Exception as e:
#         logger.error(f"Database testing failed: {e}")


# if __name__ == "__main__":
#     main()


"""
Database Utilities for ARGO Float Data - Complete Chunked Processing Version

This module handles SQLite database operations for storing and querying
ARGO float oceanographic data with chunked processing to prevent data loss.

Key features:
- Chunked processing instead of truncation (NO DATA LOSS)
- Improved memory management for large datasets
- Better error handling and progress tracking
- No time column dependency
- Minimal logging (errors only)
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import logging
from datetime import datetime
import time

# Configure minimal logging - errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class ArgoDatabase:
    """Handles SQLite database operations for ARGO float data with chunked processing."""
    
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
        """Create database tables with proper schema (no time column)."""
        try:
            # Check if database exists and has incompatible schema
            if self.db_path.exists():
                self.connection = sqlite3.connect(self.db_path)
                cursor = self.connection.cursor()
                
                # Check if old schema exists (with time column)
                try:
                    cursor.execute("PRAGMA table_info(argo_measurements)")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    if 'time' in columns:
                        print("Found incompatible database schema - recreating database")
                        self.connection.close()
                        self.db_path.unlink()  # Delete old database
                    else:
                        # Schema is compatible, just return
                        print("Database schema is compatible")
                        return
                except sqlite3.OperationalError:
                    # Table doesn't exist yet, continue with creation
                    pass
            
            # Create fresh connection
            self.connection = sqlite3.connect(self.db_path)
            cursor = self.connection.cursor()
            
            # Enable foreign key constraints and performance optimizations
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA synchronous = NORMAL")
            cursor.execute("PRAGMA cache_size = 10000")
            cursor.execute("PRAGMA temp_store = MEMORY")
            
            # Create main measurements table (NO TIME COLUMN)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS argo_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    float_id TEXT NOT NULL,
                    lat REAL NOT NULL CHECK(lat >= -90 AND lat <= 90),
                    lon REAL NOT NULL CHECK(lon >= -180 AND lon <= 180),
                    depth REAL NOT NULL CHECK(depth >= 0),
                    temp REAL CHECK(temp IS NULL OR (temp >= -5 AND temp <= 50)),
                    sal REAL CHECK(sal IS NULL OR (sal >= 0 AND sal <= 50)),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create float metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS float_metadata (
                    float_id TEXT PRIMARY KEY,
                    provider TEXT,
                    total_measurements INTEGER DEFAULT 0,
                    min_depth REAL,
                    max_depth REAL,
                    avg_depth REAL,
                    min_lat REAL,
                    max_lat REAL,
                    min_lon REAL,
                    max_lon REAL,
                    avg_temp REAL,
                    avg_sal REAL,
                    temp_measurements INTEGER DEFAULT 0,
                    sal_measurements INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create data quality table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    float_id TEXT NOT NULL,
                    file_name TEXT,
                    total_records INTEGER,
                    valid_records INTEGER,
                    invalid_coords INTEGER DEFAULT 0,
                    invalid_depth INTEGER DEFAULT 0,
                    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create performance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_float_id ON argo_measurements(float_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_location ON argo_measurements(lat, lon)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_depth ON argo_measurements(depth)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_temp ON argo_measurements(temp) WHERE temp IS NOT NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_sal ON argo_measurements(sal) WHERE sal IS NOT NULL")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_measurements_composite ON argo_measurements(float_id, depth)")
            
            self.connection.commit()
            print("Database tables and indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
        """
        Validate DataFrame before insertion - CHUNKED VERSION (no data loss).
        
        Args:
            df: Input DataFrame
            
        Returns:
            Tuple of (clean_df, validation_report)
        """
        if df.empty:
            return df, {"error": "Empty DataFrame"}
        
        original_count = len(df)
        validation_report = {
            "original_records": original_count,
            "issues_found": []
        }
        
        # Check required columns
        required_columns = ['float_id', 'lat', 'lon', 'depth']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_report["issues_found"].append(f"Missing required columns: {missing_columns}")
            return pd.DataFrame(), validation_report
        
        # Start with original data
        clean_df = df.copy()
        
        # Remove records with NULL essential fields
        before_null_check = len(clean_df)
        clean_df = clean_df.dropna(subset=['float_id', 'lat', 'lon', 'depth'])
        null_removed = before_null_check - len(clean_df)
        if null_removed > 0:
            validation_report["issues_found"].append(f"Removed {null_removed} records with NULL essential fields")
        
        # Validate coordinates
        before_coord_check = len(clean_df)
        clean_df = clean_df[
            (clean_df['lat'] >= -90) & (clean_df['lat'] <= 90) &
            (clean_df['lon'] >= -180) & (clean_df['lon'] <= 180)
        ]
        coord_removed = before_coord_check - len(clean_df)
        if coord_removed > 0:
            validation_report["issues_found"].append(f"Removed {coord_removed} records with invalid coordinates")
        
        # Validate depth
        before_depth_check = len(clean_df)
        clean_df = clean_df[(clean_df['depth'] >= 0) & (clean_df['depth'] <= 12000)]
        depth_removed = before_depth_check - len(clean_df)
        if depth_removed > 0:
            validation_report["issues_found"].append(f"Removed {depth_removed} records with invalid depth")
        
        # Validate temperature (if present)
        if 'temp' in clean_df.columns:
            before_temp_check = len(clean_df)
            # Remove records with invalid temperature (keep NULL)
            clean_df = clean_df[
                (clean_df['temp'].isnull()) | 
                ((clean_df['temp'] >= -5) & (clean_df['temp'] <= 50))
            ]
            temp_removed = before_temp_check - len(clean_df)
            if temp_removed > 0:
                validation_report["issues_found"].append(f"Removed {temp_removed} records with invalid temperature")
        
        # Validate salinity (if present)
        if 'sal' in clean_df.columns:
            before_sal_check = len(clean_df)
            # Remove records with invalid salinity (keep NULL)
            clean_df = clean_df[
                (clean_df['sal'].isnull()) | 
                ((clean_df['sal'] >= 0) & (clean_df['sal'] <= 50))
            ]
            sal_removed = before_sal_check - len(clean_df)
            if sal_removed > 0:
                validation_report["issues_found"].append(f"Removed {sal_removed} records with invalid salinity")
        
        # Clean float_id (ensure it's string and not empty)
        clean_df['float_id'] = clean_df['float_id'].astype(str)
        before_float_check = len(clean_df)
        clean_df = clean_df[clean_df['float_id'].str.strip() != '']
        float_removed = before_float_check - len(clean_df)
        if float_removed > 0:
            validation_report["issues_found"].append(f"Removed {float_removed} records with empty float_id")
        
        validation_report.update({
            "final_records": len(clean_df),
            "records_removed": original_count - len(clean_df),
            "success_rate": (len(clean_df) / original_count * 100) if original_count > 0 else 0
        })
        
        return clean_df, validation_report
    
    def insert_measurements_chunked(self, df: pd.DataFrame, chunk_size: int = 100000, batch_size: int = 5000) -> int:
        """
        CHUNKED VERSION: Insert measurements by processing large datasets in chunks.
        NO DATA LOSS - processes all data in manageable pieces.
        
        Args:
            df: DataFrame with oceanographic data
            chunk_size: Size of chunks to process data in (default 100k records)
            batch_size: Size of database insert batches (default 5k records)
            
        Returns:
            Number of rows successfully inserted
        """
        try:
            if df.empty:
                print("Empty DataFrame provided")
                return 0
            
            total_inserted = 0
            total_rows = len(df)
            
            print(f"Processing {total_rows:,} records in chunks of {chunk_size:,}")
            
            # Process data in chunks to prevent memory issues
            num_chunks = (total_rows + chunk_size - 1) // chunk_size
            
            for chunk_num in range(num_chunks):
                start_idx = chunk_num * chunk_size
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk_df = df.iloc[start_idx:end_idx].copy()
                
                print(f"Processing chunk {chunk_num + 1}/{num_chunks} ({len(chunk_df):,} records)")
                
                # Insert this chunk
                chunk_inserted = self._insert_single_chunk(chunk_df, batch_size)
                total_inserted += chunk_inserted
                
                # Progress update
                if chunk_num % 5 == 0 or chunk_num == num_chunks - 1:
                    progress = ((chunk_num + 1) / num_chunks) * 100
                    print(f"Progress: {progress:.1f}% - Inserted {total_inserted:,} / {total_rows:,} records")
            
            print(f"Chunked processing complete: {total_inserted:,} total records inserted")
            return total_inserted
            
        except Exception as e:
            logger.error(f"Error in chunked insertion: {e}")
            raise
    
    def _insert_single_chunk(self, chunk_df: pd.DataFrame, batch_size: int) -> int:
        """Insert a single chunk of data with validation and batch processing."""
        try:
            start_time = time.time()
            
            # Validate chunk
            clean_df, validation_report = self.validate_dataframe(chunk_df)
            
            # Only log validation issues if there are significant problems
            if validation_report.get('success_rate', 100) < 95:
                print(f"  Validation: {validation_report['original_records']} -> {validation_report['final_records']} records")
                for issue in validation_report['issues_found'][:3]:  # Limit output
                    print(f"    {issue}")
            
            if clean_df.empty:
                print("  No valid records in chunk after validation")
                return 0
            
            # Insert in batches
            cursor = self.connection.cursor()
            total_inserted = 0
            
            for batch_start in range(0, len(clean_df), batch_size):
                batch_end = min(batch_start + batch_size, len(clean_df))
                batch_df = clean_df.iloc[batch_start:batch_end]
                
                batch_data = []
                for idx in range(len(batch_df)):
                    try:
                        row = batch_df.iloc[idx]
                        batch_data.append((
                            str(row['float_id']).strip(),
                            float(row['lat']),
                            float(row['lon']),
                            float(row['depth']),
                            float(row['temp']) if pd.notna(row['temp']) else None,
                            float(row['sal']) if pd.notna(row['sal']) else None
                        ))
                    except Exception as e:
                        # Skip problematic rows but continue processing
                        continue
                
                if batch_data:
                    try:
                        cursor.executemany("""
                            INSERT INTO argo_measurements 
                            (float_id, lat, lon, depth, temp, sal)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, batch_data)
                        total_inserted += len(batch_data)
                    except Exception as e:
                        logger.error(f"Error inserting batch: {e}")
                        self.connection.rollback()
                        continue
            
            # Commit chunk
            self.connection.commit()
            
            # Update metadata for this chunk
            if total_inserted > 0:
                try:
                    self._update_float_metadata_for_chunk(clean_df.head(total_inserted))
                except Exception as e:
                    logger.error(f"Error updating metadata for chunk: {e}")
            
            elapsed = time.time() - start_time
            print(f"  Inserted {total_inserted:,} records in {elapsed:.1f}s")
            
            return total_inserted
            
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            if self.connection:
                self.connection.rollback()
            return 0
    
    def insert_measurements(self, df: pd.DataFrame, batch_size: int = 5000) -> int:
        """
        Legacy method - now uses chunked processing automatically for large datasets.
        
        Args:
            df: DataFrame with oceanographic data
            batch_size: Number of records to insert per batch
            
        Returns:
            Number of rows successfully inserted
        """
        # Automatically use chunked processing for datasets > 50k records
        if len(df) > 50000:
            print(f"Large dataset detected ({len(df):,} records), using chunked processing")
            return self.insert_measurements_chunked(df, chunk_size=100000, batch_size=batch_size)
        else:
            return self._insert_single_chunk(df, batch_size)
    
    def _update_float_metadata_for_chunk(self, df: pd.DataFrame):
        """Update float metadata for a chunk of data."""
        try:
            cursor = self.connection.cursor()
            unique_floats = df['float_id'].unique()
            
            for float_id in unique_floats:
                try:
                    float_data = df[df['float_id'] == float_id]
                    
                    if len(float_data) == 0:
                        continue
                    
                    # Calculate statistics
                    stats = {
                        'total_measurements': len(float_data),
                        'min_depth': float_data['depth'].min(),
                        'max_depth': float_data['depth'].max(),
                        'avg_depth': float_data['depth'].mean(),
                        'min_lat': float_data['lat'].min(),
                        'max_lat': float_data['lat'].max(),
                        'min_lon': float_data['lon'].min(),
                        'max_lon': float_data['lon'].max(),
                        'temp_measurements': float_data['temp'].notna().sum(),
                        'sal_measurements': float_data['sal'].notna().sum(),
                        'avg_temp': float_data['temp'].mean() if float_data['temp'].notna().any() else None,
                        'avg_sal': float_data['sal'].mean() if float_data['sal'].notna().any() else None
                    }
                    
                    # Use INSERT OR IGNORE to handle concurrent updates
                    cursor.execute("""
                        INSERT OR REPLACE INTO float_metadata 
                        (float_id, total_measurements, min_depth, max_depth, avg_depth,
                         min_lat, max_lat, min_lon, max_lon, avg_temp, avg_sal,
                         temp_measurements, sal_measurements, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        str(float_id),
                        stats['total_measurements'],
                        stats['min_depth'],
                        stats['max_depth'],
                        stats['avg_depth'],
                        stats['min_lat'],
                        stats['max_lat'],
                        stats['min_lon'],
                        stats['max_lon'],
                        stats['avg_temp'],
                        stats['avg_sal'],
                        stats['temp_measurements'],
                        stats['sal_measurements']
                    ))
                except Exception as e:
                    logger.error(f"Error updating metadata for float {float_id}: {e}")
            
            # Commit metadata updates
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Error updating float metadata: {e}")
    
    def get_measurements_by_bbox(self, min_lat: float, max_lat: float, 
                               min_lon: float, max_lon: float, 
                               limit: int = None) -> pd.DataFrame:
        """Get measurements within a bounding box."""
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE lat BETWEEN ? AND ? 
                AND lon BETWEEN ? AND ?
                ORDER BY float_id, depth
            """
            params = [min_lat, max_lat, min_lon, max_lon]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            df = pd.read_sql_query(query, self.connection, params=params)
            print(f"Retrieved {len(df)} measurements in bounding box")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by bounding box: {e}")
            return pd.DataFrame()
    
    def get_measurements_by_depth_range(self, min_depth: float, max_depth: float,
                                      limit: int = None) -> pd.DataFrame:
        """Get measurements within a depth range."""
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE depth BETWEEN ? AND ?
                ORDER BY float_id, depth
            """
            params = [min_depth, max_depth]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            df = pd.read_sql_query(query, self.connection, params=params)
            print(f"Retrieved {len(df)} measurements in depth range {min_depth}-{max_depth}m")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by depth range: {e}")
            return pd.DataFrame()
    
    def get_measurements_by_parameter(self, parameter: str, min_value: float, max_value: float,
                                    limit: int = None) -> pd.DataFrame:
        """Get measurements within a parameter value range."""
        try:
            if parameter not in ['temp', 'sal']:
                raise ValueError("Parameter must be 'temp' or 'sal'")
            
            query = f"""
                SELECT * FROM argo_measurements 
                WHERE {parameter} BETWEEN ? AND ?
                AND {parameter} IS NOT NULL
                ORDER BY float_id, depth
            """
            params = [min_value, max_value]
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            df = pd.read_sql_query(query, self.connection, params=params)
            print(f"Retrieved {len(df)} measurements with {parameter} in range {min_value}-{max_value}")
            return df
            
        except Exception as e:
            logger.error(f"Error querying by parameter: {e}")
            return pd.DataFrame()
    
    def get_float_profile(self, float_id: str) -> pd.DataFrame:
        """Get complete profile for a specific float."""
        try:
            query = """
                SELECT * FROM argo_measurements 
                WHERE float_id = ?
                ORDER BY depth
            """
            
            df = pd.read_sql_query(query, self.connection, params=[str(float_id)])
            print(f"Retrieved {len(df)} measurements for float {float_id}")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving float profile: {e}")
            return pd.DataFrame()
    
    def get_float_summary(self) -> pd.DataFrame:
        """Get comprehensive summary for all floats."""
        try:
            query = """
                SELECT 
                    m.float_id,
                    COUNT(*) as total_measurements,
                    MIN(m.lat) as min_lat,
                    MAX(m.lat) as max_lat,
                    MIN(m.lon) as min_lon,
                    MAX(m.lon) as max_lon,
                    MIN(m.depth) as min_depth,
                    MAX(m.depth) as max_depth,
                    AVG(m.depth) as avg_depth,
                    COUNT(CASE WHEN m.temp IS NOT NULL THEN 1 END) as temp_count,
                    COUNT(CASE WHEN m.sal IS NOT NULL THEN 1 END) as sal_count,
                    AVG(m.temp) as avg_temp,
                    AVG(m.sal) as avg_sal,
                    MIN(m.temp) as min_temp,
                    MAX(m.temp) as max_temp,
                    MIN(m.sal) as min_sal,
                    MAX(m.sal) as max_sal
                FROM argo_measurements m
                GROUP BY m.float_id
                ORDER BY m.float_id
            """
            
            df = pd.read_sql_query(query, self.connection)
            print(f"Retrieved summary for {len(df)} floats")
            return df
            
        except Exception as e:
            logger.error(f"Error retrieving float summary: {e}")
            return pd.DataFrame()
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics."""
        try:
            cursor = self.connection.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM argo_measurements")
            total_measurements = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT float_id) FROM argo_measurements")
            unique_floats = cursor.fetchone()[0]
            
            # Data completeness
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN temp IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as temp_completeness,
                    COUNT(CASE WHEN sal IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as sal_completeness,
                    COUNT(CASE WHEN temp IS NOT NULL AND sal IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as both_complete
                FROM argo_measurements
            """)
            result = cursor.fetchone()
            temp_comp, sal_comp, both_comp = result if result else (0, 0, 0)
            
            # Geographic coverage
            cursor.execute("""
                SELECT MIN(lat), MAX(lat), MIN(lon), MAX(lon),
                       MIN(depth), MAX(depth), AVG(depth)
                FROM argo_measurements
            """)
            geo_result = cursor.fetchone()
            min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, avg_depth = geo_result if geo_result else (0, 0, 0, 0, 0, 0, 0)
            
            # Parameter ranges
            cursor.execute("""
                SELECT MIN(temp), MAX(temp), AVG(temp),
                       MIN(sal), MAX(sal), AVG(sal)
                FROM argo_measurements
                WHERE temp IS NOT NULL OR sal IS NOT NULL
            """)
            param_result = cursor.fetchone()
            
            # Database file size
            db_size_mb = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
            
            return {
                "database_file": str(self.db_path),
                "database_size_mb": round(db_size_mb, 2),
                "total_measurements": total_measurements,
                "unique_floats": unique_floats,
                "avg_measurements_per_float": round(total_measurements / unique_floats, 1) if unique_floats > 0 else 0,
                "data_completeness": {
                    "temperature": round(temp_comp, 2) if temp_comp else 0,
                    "salinity": round(sal_comp, 2) if sal_comp else 0,
                    "both_parameters": round(both_comp, 2) if both_comp else 0
                },
                "geographic_coverage": {
                    "latitude_range": [round(min_lat, 3), round(max_lat, 3)] if min_lat else [0, 0],
                    "longitude_range": [round(min_lon, 3), round(max_lon, 3)] if min_lon else [0, 0],
                },
                "depth_statistics": {
                    "range": [round(min_depth, 1), round(max_depth, 1)] if min_depth else [0, 0],
                    "average": round(avg_depth, 1) if avg_depth else 0
                },
                "parameter_ranges": {
                    "temperature": [round(param_result[0], 2), round(param_result[1], 2)] if param_result and param_result[0] else None,
                    "salinity": [round(param_result[3], 2), round(param_result[4], 2)] if param_result and param_result[3] else None
                } if param_result else None
            }
            
        except Exception as e:
            logger.error(f"Error generating database statistics: {e}")
            return {"error": str(e)}
    
    def optimize_database(self):
        """Optimize database performance."""
        try:
            cursor = self.connection.cursor()
            
            print("Optimizing database...")
            
            # Update table statistics
            cursor.execute("ANALYZE")
            
            # Vacuum database to reclaim space
            cursor.execute("VACUUM")
            
            self.connection.commit()
            print("Database optimization completed")
            
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """Test database functionality with chunked processing."""
    try:
        print("Testing chunked database operations...")
        
        # Create larger test dataset to demonstrate chunking
        test_data = pd.DataFrame({
            'float_id': ['1234567'] * 5000 + ['2345678'] * 5000,  # 10k records for testing
            'lat': [45.0 + i*0.001 for i in range(10000)],
            'lon': [-120.0 + i*0.001 for i in range(10000)],
            'depth': [i*0.5 for i in range(10000)],
            'temp': [15.5 - i*0.001 for i in range(10000)],
            'sal': [35.0 + np.random.random(10000) * 0.5]
        })
        
        with ArgoDatabase("test_chunked_argo.db") as db:
            print("Starting chunked insertion test...")
            inserted = db.insert_measurements_chunked(test_data, chunk_size=3000, batch_size=1000)
            print(f"Inserted {inserted} test records using chunked processing")
            
            # Test queries
            summary = db.get_float_summary()
            print(f"Float summary: {len(summary)} floats found")
            
            stats = db.get_database_stats()
            print(f"Database stats: {stats.get('total_measurements', 0)} total measurements")
            
        # Clean up test database
        test_db_path = Path("test_chunked_argo.db")
        if test_db_path.exists():
            test_db_path.unlink()
            print("Cleaned up test database")
        
        print("Chunked database testing completed successfully")
        
    except Exception as e:
        logger.error(f"Database testing failed: {e}")


if __name__ == "__main__":
    main()