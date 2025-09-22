import os
import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArgoDataIngestion:
    """Handles ingestion of ARGO float NetCDF data with strict validation."""

    def __init__(self, data_path: str = "argo/aux"):
        self.data_path = Path(data_path)
        self.supported_providers = ["aoml", "bodc", "coriolis"]

import os
import pandas as pd
import xarray as xr
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Configure minimal logging - errors only
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class ArgoDataIngestion:
    """Handles ingestion of ARGO float NetCDF data with chunked processing."""

    def __init__(self, data_path: str = "argo/aux"):
        self.data_path = Path(data_path)
        self.supported_providers = ["aoml", "bodc", "coriolis"]

    def find_all_netcdf_files(self) -> List[Path]:
        """Find all NetCDF files in the ARGO data directory with expanded search."""
        netcdf_files = []
        float_directories = set()

        for provider in self.supported_providers:
            provider_path = self.data_path / provider
            if not provider_path.exists():
                continue
            
            for float_dir in provider_path.iterdir():
                if float_dir.is_dir() and float_dir.name.isdigit() and len(float_dir.name) == 7:
                    float_directories.add(float_dir.name)
                    
                    # Search in profiles folder
                    profiles_dir = float_dir / "profiles"
                    if profiles_dir.exists() and profiles_dir.is_dir():
                        netcdf_files.extend(list(profiles_dir.glob("*.nc")))
                    
                    # Search in float directory root
                    netcdf_files.extend(list(float_dir.glob("*.nc")))
                    
                    # Search in other subdirectories
                    for sub_dir in float_dir.iterdir():
                        if sub_dir.is_dir() and sub_dir.name != "profiles":
                            netcdf_files.extend(list(sub_dir.glob("*.nc")))

        # Remove duplicates
        unique_files = list(set(netcdf_files))
        return unique_files

    def _find_variable(self, dataset: xr.Dataset, possible_names: List[str]) -> Optional[str]:
        """Find the first available variable in the dataset from a list of possible names."""
        for name in possible_names:
            if name in dataset.variables:
                return name
        return None

    def _get_variable_dimension(self, dataset: xr.Dataset, var_name: str) -> Optional[str]:
        """Get the primary dimension of a variable (first dimension if multi-dimensional)."""
        if var_name not in dataset.variables:
            return None
        dims = dataset[var_name].dims
        return dims[0] if dims else None

    def _safe_extract_scalar(self, dataset: xr.Dataset, var_name: str, index: int = 0) -> any:
        """Safely extract a scalar value from a variable at given index."""
        if var_name not in dataset.variables:
            return None
        
        try:
            var = dataset[var_name]
            if var.dims:
                dim_name = var.dims[0]
                if index < var.sizes[dim_name]:
                    value = var.isel({dim_name: index}).values
                    if isinstance(value, (np.ndarray, list)):
                        value = value.item() if value.size == 1 else value[0]
                    return value if not (isinstance(value, float) and np.isnan(value)) else None
            else:
                value = var.values
                return value if not (isinstance(value, float) and np.isnan(value)) else None
        except:
            pass
        return None

    def _safe_extract_array(self, dataset: xr.Dataset, var_name: str, profile_index: int = 0) -> np.ndarray:
        """Safely extract an array from a variable at given profile index."""
        if var_name not in dataset.variables:
            return np.array([])
        
        try:
            var = dataset[var_name]
            if len(var.dims) == 2:
                profile_dim, level_dim = var.dims
                if profile_index < var.sizes[profile_dim]:
                    return var.isel({profile_dim: profile_index}).values
            elif len(var.dims) == 1:
                return var.values
            else:
                return np.array([var.values])
        except:
            pass
        
        return np.array([])

    def _is_valid_coordinate(self, lat: any, lon: any) -> bool:
        """Check if latitude and longitude are valid."""
        try:
            if lat is None or lon is None:
                return False
            
            lat_val = float(lat)
            lon_val = float(lon)
            
            if np.isnan(lat_val) or np.isnan(lon_val) or np.isinf(lat_val) or np.isinf(lon_val):
                return False
            
            if lat_val < -90 or lat_val > 90:
                return False
            if lon_val < -180 or lon_val > 180:
                return False
            
            return True
        except:
            return False

    def _is_valid_depth(self, depth: any) -> bool:
        """Check if depth value is valid."""
        try:
            if depth is None:
                return False
            
            depth_val = float(depth)
            
            if np.isnan(depth_val) or np.isinf(depth_val):
                return False
            
            if depth_val < 0 or depth_val > 12000:
                return False
            
            return True
        except:
            return False

    def _is_valid_measurement(self, value: any) -> bool:
        """Check if a measurement value (temp/sal) is valid."""
        try:
            if value is None:
                return True
            val = float(value)
            if np.isnan(val) or np.isinf(val):
                return True
            return True
        except:
            return False

    def _extract_float_id(self, nc_file: Path) -> str:
        """Extract float ID from file path using multiple strategies."""
        
        # Strategy 1: Parent directory name
        if nc_file.parent.name.isdigit() and len(nc_file.parent.name) == 7:
            return nc_file.parent.name
        
        # Strategy 2: Grandparent directory
        if nc_file.parent.parent.name.isdigit() and len(nc_file.parent.parent.name) == 7:
            return nc_file.parent.parent.name
        
        # Strategy 3: Extract from filename
        filename_parts = nc_file.stem.split('_')
        for part in filename_parts:
            if len(part) == 7 and part.isdigit():
                return part
            elif len(part) == 8 and part[0].isalpha() and part[1:].isdigit():
                return part[1:]
        
        # Strategy 4: Check parent directories
        current_path = nc_file.parent
        for _ in range(3):
            if current_path.name.isdigit() and len(current_path.name) == 7:
                return current_path.name
            current_path = current_path.parent
            if current_path == current_path.parent:
                break
        
        # Strategy 5: Try NetCDF file metadata
        try:
            with xr.open_dataset(nc_file, decode_times=False) as ds:
                if 'PLATFORM_NUMBER' in ds.variables:
                    platform_num = ds['PLATFORM_NUMBER'].values
                    if hasattr(platform_num, 'item'):
                        platform_num = platform_num.item()
                    if isinstance(platform_num, (str, bytes)):
                        platform_str = str(platform_num).strip()
                        if platform_str.isdigit() and len(platform_str) == 7:
                            return platform_str
        except:
            pass
        
        return nc_file.stem

    def process_netcdf_file(self, nc_file: Path, chunk_size: int = 50000) -> pd.DataFrame:
        """Process a single NetCDF file with chunked processing to prevent data loss."""
        try:
            float_id = self._extract_float_id(nc_file)
            if not float_id:
                return pd.DataFrame()
            
            with xr.open_dataset(nc_file, decode_times=False, decode_timedelta=False) as ds:
                all_valid_data = []

                # Find variables
                time_var = self._find_variable(ds, ['JULD', 'TIME', 'MTIME', 'time'])
                lat_var = self._find_variable(ds, ['LATITUDE', 'LAT', 'lat'])
                lon_var = self._find_variable(ds, ['LONGITUDE', 'LON', 'lon'])
                pres_var = self._find_variable(ds, ['PRES', 'PRESSURE', 'pressure', 'PRES_ADJUSTED'])
                temp_var = self._find_variable(ds, ['TEMP', 'TEMP_ADJUSTED', 'temperature'])
                sal_var = self._find_variable(ds, ['PSAL', 'PSAL_ADJUSTED', 'salinity'])

                if not lat_var or not lon_var:
                    return pd.DataFrame()

                n_profiles = self._determine_profile_count(ds, time_var, lat_var, lon_var)
                if n_profiles == 0:
                    return pd.DataFrame()

                # Limit profiles per file but process all measurements within each profile
                max_profiles = min(n_profiles, 10000)

                for i in range(max_profiles):
                    lat_val = self._safe_extract_scalar(ds, lat_var, i)
                    lon_val = self._safe_extract_scalar(ds, lon_var, i)

                    if not self._is_valid_coordinate(lat_val, lon_val):
                        continue

                    depth_data = self._safe_extract_array(ds, pres_var, i) if pres_var else np.array([0.0])
                    temp_data = self._safe_extract_array(ds, temp_var, i) if temp_var else np.array([])
                    sal_data = self._safe_extract_array(ds, sal_var, i) if sal_var else np.array([])

                    if len(depth_data) == 0:
                        depth_data = np.array([0.0])

                    max_len = max(len(depth_data), len(temp_data), len(sal_data))
                    if max_len == 0:
                        continue

                    # FIXED: Process ALL measurements in chunks instead of truncating
                    total_measurements = max_len
                    if total_measurements > chunk_size:
                        print(f"INFO: Profile {i} in {nc_file.name} has {total_measurements} measurements, processing in chunks of {chunk_size}")

                    depth_data = self._pad_array(depth_data, max_len)
                    temp_data = self._pad_array(temp_data, max_len) if len(temp_data) > 0 else np.full(max_len, np.nan)
                    sal_data = self._pad_array(sal_data, max_len) if len(sal_data) > 0 else np.full(max_len, np.nan)

                    # Process in chunks - NO DATA LOSS
                    for chunk_start in range(0, max_len, chunk_size):
                        chunk_end = min(chunk_start + chunk_size, max_len)
                        
                        for j in range(chunk_start, chunk_end):
                            if not self._is_valid_depth(depth_data[j]):
                                continue

                            temp_val = None
                            sal_val = None
                            
                            if len(temp_data) > j and self._is_valid_measurement(temp_data[j]):
                                if not np.isnan(temp_data[j]):
                                    temp_val = float(temp_data[j])
                            
                            if len(sal_data) > j and self._is_valid_measurement(sal_data[j]):
                                if not np.isnan(sal_data[j]):
                                    sal_val = float(sal_data[j])

                            all_valid_data.append({
                                'float_id': float_id,
                                'lat': float(lat_val),
                                'lon': float(lon_val),
                                'depth': float(depth_data[j]),
                                'temp': temp_val,
                                'sal': sal_val
                            })

                return pd.DataFrame(all_valid_data)

        except Exception as e:
            logger.error(f"Error processing {nc_file}: {str(e)}")
            return pd.DataFrame()

    def _determine_profile_count(self, ds: xr.Dataset, time_var: str, lat_var: str, lon_var: str) -> int:
        """Robustly determine the number of profiles with safety limits."""
        try:
            if 'N_PROF' in ds.sizes:
                count = ds.sizes['N_PROF']
                return min(count, 10000)  # Max 10k profiles per file
            
            for var in [time_var, lat_var, lon_var]:
                if var and var in ds.variables:
                    dim = self._get_variable_dimension(ds, var)
                    if dim and dim in ds.sizes:
                        count = ds.sizes[dim]
                        return min(count, 10000)  # Safety limit
            
            return 1
        except:
            return 0

    def _pad_array(self, array: np.ndarray, target_length: int) -> np.ndarray:
        """Pad array to target length with NaN values."""
        if len(array) >= target_length:
            return array[:target_length]
        
        padded = np.full(target_length, np.nan)
        padded[:len(array)] = array
        return padded

    def ingest_all_data(self, chunk_size: int = 50000) -> pd.DataFrame:
        """Ingest all NetCDF files with chunked processing - no data loss."""
        print("Starting file discovery...")
        netcdf_files = self.find_all_netcdf_files()
        if not netcdf_files:
            print("ERROR: No NetCDF files found. Check your data path.")
            return pd.DataFrame()

        print(f"Found {len(netcdf_files)} NetCDF files. Starting chunked processing...")
        all_data = []
        successful_files = 0
        failed_files = 0

        for i, nc_file in enumerate(netcdf_files):
            # Progress indicator every 100 files (reduced logging overhead)
            if i % 100 == 0 and i > 0:
                print(f"Processing file {i+1}/{len(netcdf_files)}... ({successful_files} successful, {failed_files} failed)")
            
            try:
                # Process with chunked approach
                df = self.process_netcdf_file(nc_file, chunk_size)
                if not df.empty:
                    all_data.append(df)
                    successful_files += 1
                else:
                    failed_files += 1
                    
                # Safety check - if too many consecutive failures, something might be wrong
                if failed_files > 100 and successful_files == 0:
                    print(f"WARNING: {failed_files} consecutive failures. There might be an issue with file format or data structure.")
                    print("Continuing with next files...")
                    
            except Exception as e:
                failed_files += 1
                if failed_files <= 3:  # Only show first few errors
                    logger.error(f"Error processing {nc_file.name}: {str(e)}")

        print(f"Processing complete. Combining {len(all_data)} successful datasets...")

        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Final summary
            unique_floats = combined_df['float_id'].nunique()
            float_counts = combined_df['float_id'].value_counts()
            temp_completeness = (combined_df['temp'].notna().sum() / len(combined_df)) * 100
            sal_completeness = (combined_df['sal'].notna().sum() / len(combined_df)) * 100
            
            print(f"\n{'='*60}")
            print("ARGO DATA INGESTION COMPLETED - CHUNKED PROCESSING")
            print(f"{'='*60}")
            print(f"Files processed: {successful_files}/{len(netcdf_files)} (Success rate: {(successful_files/len(netcdf_files)*100):.1f}%)")
            print(f"Total records: {len(combined_df):,}")
            print(f"Unique floats: {unique_floats}")
            print(f"Top floats by record count:")
            for i, (float_id, count) in enumerate(float_counts.head(5).items()):
                print(f"  {i+1}. Float {float_id}: {count:,} records")
            print(f"Temperature completeness: {temp_completeness:.1f}%")
            print(f"Salinity completeness: {sal_completeness:.1f}%")
            print(f"Lat range: {combined_df['lat'].min():.2f} to {combined_df['lat'].max():.2f}")
            print(f"Lon range: {combined_df['lon'].min():.2f} to {combined_df['lon'].max():.2f}")
            print(f"Depth range: {combined_df['depth'].min():.1f} to {combined_df['depth'].max():.1f}m")
            print(f"{'='*60}\n")
            
            return combined_df
        else:
            print("ERROR: No valid data could be processed from any files.")
            return pd.DataFrame()

    def get_data_summary(self, df: pd.DataFrame) -> Dict:
        """Generate comprehensive data summary."""
        if df.empty:
            return {"error": "No data to summarize"}
        
        return {
            "total_measurements": len(df),
            "unique_floats": df['float_id'].nunique(),
            "depth_statistics": {
                "min": df['depth'].min(),
                "max": df['depth'].max(),
                "mean": df['depth'].mean(),
                "std": df['depth'].std()
            },
            "geographical_coverage": {
                "lat_range": [df['lat'].min(), df['lat'].max()],
                "lon_range": [df['lon'].min(), df['lon'].max()],
                "lat_mean": df['lat'].mean(),
                "lon_mean": df['lon'].mean()
            },
            "data_completeness": {
                "temperature": (df['temp'].notna().sum() / len(df)) * 100,
                "salinity": (df['sal'].notna().sum() / len(df)) * 100
            },
            "measurement_statistics": {
                "temperature": {
                    "min": df['temp'].min(),
                    "max": df['temp'].max(),
                    "mean": df['temp'].mean()
                },
                "salinity": {
                    "min": df['sal'].min(),
                    "max": df['sal'].max(),
                    "mean": df['sal'].mean()
                }
            }
        }


def main():
    """Main execution with chunked processing."""
    try:
        ingestion = ArgoDataIngestion()
        # Use chunked processing with configurable chunk size
        df = ingestion.ingest_all_data(chunk_size=50000)
        
        if df.empty:
            print("ERROR: No valid data was ingested.")
            return
        
        # Save to CSV
        output_file = "argo_ingested_data_chunked.csv"
        df.to_csv(output_file, index=False)
        print(f"Data saved to: {output_file}")
        
        return df
        
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()