"""
Data Ingestion Module for ARGO Float Data

This module handles reading NetCDF files from ARGO floats and converting them
into tabular format for database storage.

In the final SIH PoC, this will be extended with:
- Large dataset ingestion capabilities
- Parallel processing for multiple floats
- Additional sensor data (oxygen, nitrate, etc.)
- Real-time data streaming
"""

import os
import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArgoDataIngestion:
    """Handles ingestion of ARGO float NetCDF data."""
    
    def __init__(self, data_path: str = "argo/aux"):
        """
        Initialize the data ingestion class.
        
        Args:
            data_path: Path to the ARGO data directory
        """
        self.data_path = Path(data_path)
        self.supported_providers = ["aoml", "bodc", "coriolis"]
        
    def find_netcdf_files(self, max_files: int = 3) -> List[Path]:
        """
        Find NetCDF files in the ARGO data directory.
        
        Args:
            max_files: Maximum number of files to return
            
        Returns:
            List of NetCDF file paths
        """
        netcdf_files = []
        
        for provider in self.supported_providers:
            provider_path = self.data_path / provider
            if not provider_path.exists():
                logger.warning(f"Provider directory not found: {provider_path}")
                continue
                
            # Find float directories (7-digit WMO IDs)
            for float_dir in provider_path.iterdir():
                if float_dir.is_dir() and float_dir.name.isdigit() and len(float_dir.name) == 7:
                    # Look for NetCDF files
                    for nc_file in float_dir.glob("*_meta_aux.nc"):
                        netcdf_files.append(nc_file)
                    for nc_file in float_dir.glob("*_tech_aux.nc"):
                        netcdf_files.append(nc_file)
                        
                    if len(netcdf_files) >= max_files:
                        break
                        
            if len(netcdf_files) >= max_files:
                break
                
        logger.info(f"Found {len(netcdf_files)} NetCDF files")
        return netcdf_files[:max_files]
    
    def extract_float_metadata(self, nc_file: Path) -> Dict:
        """
        Extract metadata from NetCDF file.
        
        Args:
            nc_file: Path to NetCDF file
            
        Returns:
            Dictionary containing float metadata
        """
        try:
            with xr.open_dataset(nc_file) as ds:
                metadata = {
                    'float_id': nc_file.parent.name,
                    'provider': nc_file.parent.parent.name,
                    'file_type': 'meta' if '_meta_aux.nc' in nc_file.name else 'tech',
                    'file_path': str(nc_file)
                }
                
                # Extract additional metadata if available
                if hasattr(ds, 'PLATFORM_NUMBER'):
                    metadata['platform_number'] = str(ds.PLATFORM_NUMBER.values)
                if hasattr(ds, 'WMO_INST_TYPE'):
                    metadata['wmo_type'] = str(ds.WMO_INST_TYPE.values)
                    
                return metadata
                
        except Exception as e:
            logger.error(f"Error extracting metadata from {nc_file}: {e}")
            return {}
    
    def process_netcdf_file(self, nc_file: Path) -> pd.DataFrame:
        """
        Process a single NetCDF file and extract oceanographic data.
        
        Args:
            nc_file: Path to NetCDF file
            
        Returns:
            DataFrame with oceanographic measurements
        """
        try:
            with xr.open_dataset(nc_file) as ds:
                # Extract float ID from directory name
                float_id = nc_file.parent.name
                
                # Initialize data dictionary
                data = {
                    'float_id': [],
                    'time': [],
                    'lat': [],
                    'lon': [],
                    'depth': [],
                    'temp': [],
                    'sal': []
                }
                
                # Extract variables based on available data
                # Handle different variable names that might exist
                time_var = self._find_variable(ds, ['TIME', 'JULD', 'time'])
                lat_var = self._find_variable(ds, ['LATITUDE', 'LAT', 'lat'])
                lon_var = self._find_variable(ds, ['LONGITUDE', 'LON', 'lon'])
                pres_var = self._find_variable(ds, ['PRES', 'PRESSURE', 'pressure'])
                temp_var = self._find_variable(ds, ['TEMP', 'TEMP_ADJUSTED', 'temperature'])
                sal_var = self._find_variable(ds, ['PSAL', 'PSAL_ADJUSTED', 'salinity'])
                
                # Process data if variables are found
                if all(var is not None for var in [time_var, lat_var, lon_var]):
                    # Get dimensions
                    n_profiles = len(ds[time_var])
                    
                    for i in range(n_profiles):
                        # Extract profile data
                        time_val = ds[time_var].isel({time_var: i}).values
                        lat_val = ds[lat_var].isel({lat_var: i}).values
                        lon_val = ds[lon_var].isel({lon_var: i}).values
                        
                        # Handle pressure/depth data
                        if pres_var is not None:
                            pres_data = ds[pres_var].isel({pres_var: i}).values
                            # Convert pressure to depth (approximate: 1 dbar ≈ 1 meter)
                            depth_data = pres_data
                        else:
                            depth_data = np.array([0])  # Surface measurement
                        
                        # Handle temperature data
                        if temp_var is not None:
                            temp_data = ds[temp_var].isel({temp_var: i}).values
                        else:
                            temp_data = np.full_like(depth_data, np.nan)
                        
                        # Handle salinity data
                        if sal_var is not None:
                            sal_data = ds[sal_var].isel({sal_var: i}).values
                        else:
                            sal_data = np.full_like(depth_data, np.nan)
                        
                        # Ensure all arrays have the same length
                        max_len = max(len(depth_data), len(temp_data), len(sal_data))
                        
                        # Pad arrays to same length
                        depth_data = np.pad(depth_data, (0, max_len - len(depth_data)), 
                                          constant_values=np.nan)
                        temp_data = np.pad(temp_data, (0, max_len - len(temp_data)), 
                                         constant_values=np.nan)
                        sal_data = np.pad(sal_data, (0, max_len - len(sal_data)), 
                                        constant_values=np.nan)
                        
                        # Add data points
                        for j in range(max_len):
                            if not np.isnan(depth_data[j]):
                                data['float_id'].append(float_id)
                                data['time'].append(pd.to_datetime(time_val))
                                data['lat'].append(float(lat_val))
                                data['lon'].append(float(lon_val))
                                data['depth'].append(float(depth_data[j]))
                                data['temp'].append(float(temp_data[j]) if not np.isnan(temp_data[j]) else None)
                                data['sal'].append(float(sal_data[j]) if not np.isnan(sal_data[j]) else None)
                
                df = pd.DataFrame(data)
                logger.info(f"Processed {len(df)} data points from {nc_file}")
                return df
                
        except Exception as e:
            logger.error(f"Error processing {nc_file}: {e}")
            return pd.DataFrame()
    
    def _find_variable(self, dataset: xr.Dataset, possible_names: List[str]) -> Optional[str]:
        """
        Find a variable in the dataset by trying different possible names.
        
        Args:
            dataset: xarray Dataset
            possible_names: List of possible variable names
            
        Returns:
            Variable name if found, None otherwise
        """
        for name in possible_names:
            if name in dataset.variables:
                return name
        return None
    
    def ingest_sample_data(self, max_files: int = 3) -> pd.DataFrame:
        """
        Ingest sample data from multiple NetCDF files.
        
        Args:
            max_files: Maximum number of files to process
            
        Returns:
            Combined DataFrame with all oceanographic data
        """
        netcdf_files = self.find_netcdf_files(max_files)
        
        if not netcdf_files:
            logger.warning("No NetCDF files found. Creating sample data for demonstration.")
            return self._create_sample_data()
        
        all_data = []
        
        for nc_file in netcdf_files:
            logger.info(f"Processing {nc_file}")
            df = self.process_netcdf_file(nc_file)
            if not df.empty:
                all_data.append(df)
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Successfully ingested {len(combined_df)} total data points")
            return combined_df
        else:
            logger.warning("No data could be processed. Creating sample data for demonstration.")
            return self._create_sample_data()
    
    def _create_sample_data(self) -> pd.DataFrame:
        """
        Create sample ARGO float data for demonstration purposes.
        
        Returns:
            DataFrame with sample oceanographic data
        """
        logger.info("Creating sample ARGO float data for demonstration")
        
        # Sample float IDs
        float_ids = ['1901234', '1901235', '1901236']
        
        data = []
        
        for float_id in float_ids:
            # Generate sample profiles
            n_profiles = np.random.randint(5, 15)
            
            for profile in range(n_profiles):
                # Random location (ocean-like coordinates)
                lat = np.random.uniform(-60, 60)
                lon = np.random.uniform(-180, 180)
                
                # Random time in 2023
                time = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
                
                # Generate depth profile (0 to 2000m)
                depths = np.linspace(0, 2000, np.random.randint(20, 50))
                
                # Generate realistic temperature profile
                temp_surface = np.random.uniform(15, 30)
                temp_deep = np.random.uniform(2, 8)
                temp_profile = temp_surface + (temp_deep - temp_surface) * (depths / 2000) ** 0.5
                temp_profile += np.random.normal(0, 0.5, len(depths))
                
                # Generate realistic salinity profile
                sal_surface = np.random.uniform(34, 36)
                sal_deep = np.random.uniform(34.5, 35.5)
                sal_profile = sal_surface + (sal_deep - sal_surface) * (depths / 2000) ** 0.3
                sal_profile += np.random.normal(0, 0.1, len(depths))
                
                # Add data points
                for i, depth in enumerate(depths):
                    data.append({
                        'float_id': float_id,
                        'time': time,
                        'lat': lat,
                        'lon': lon,
                        'depth': depth,
                        'temp': temp_profile[i],
                        'sal': sal_profile[i]
                    })
        
        df = pd.DataFrame(data)
        logger.info(f"Created {len(df)} sample data points")
        return df


def main():
    """Test the data ingestion functionality."""
    ingestion = ArgoDataIngestion()
    df = ingestion.ingest_sample_data(max_files=3)
    
    print(f"Data shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Float IDs: {df['float_id'].unique()}")
    print(f"Date range: {df['time'].min()} to {df['time'].max()}")
    print(f"Depth range: {df['depth'].min():.1f}m to {df['depth'].max():.1f}m")
    print(f"Temperature range: {df['temp'].min():.2f}°C to {df['temp'].max():.2f}°C")
    print(f"Salinity range: {df['sal'].min():.2f} to {df['sal'].max():.2f}")


if __name__ == "__main__":
    main()
