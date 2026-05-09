"""Centralized data-loading and ingestion limits for the FloatChat prototype.

Adjust the active preset in one place to scale the entire project up or down.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
import os
from typing import Dict, Tuple


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DataConfig:
    """Grouped limits that control ingestion, sampling, and query truncation."""

    name: str
    max_files: int
    chunk_size: int
    max_profiles_per_file: int
    db_sample_limit: int
    dataframe_sample_limit: int
    float_profile_sample_limit: int
    float_profile_bin_count: int
    float_profile_sample_per_bin: int
    query_example_limit: int
    top_float_display_limit: int
    db_stats_primary_rowid_stride: int
    db_stats_primary_sample_limit: int
    db_stats_fallback_rowid_stride: int
    db_stats_fallback_sample_limit: int
    summary_rowid_stride: int
    summary_float_limit: int
    sample_data_rowid_stride: int
    sample_data_points_per_grid_cell: int
    float_profile_downsample_threshold: int
    validation_issue_preview_limit: int
    db_insert_chunk_size: int
    db_insert_batch_size: int
    db_insert_large_dataset_threshold: int
    test_dataset_total_rows: int
    test_dataset_float_rows: int
    test_insert_chunk_size: int
    test_insert_batch_size: int
    sample_profile_rate_thresholds: Tuple[Tuple[int, int], ...]


SMALL_TEST = DataConfig(
    name="SMALL_TEST",
    max_files=2,
    chunk_size=5_000,
    max_profiles_per_file=100,
    db_sample_limit=5_000,
    dataframe_sample_limit=5_000,
    float_profile_sample_limit=5_000,
    float_profile_bin_count=25,
    float_profile_sample_per_bin=5,
    query_example_limit=5,
    top_float_display_limit=5,
    db_stats_primary_rowid_stride=1_000,
    db_stats_primary_sample_limit=1_000,
    db_stats_fallback_rowid_stride=100,
    db_stats_fallback_sample_limit=10_000,
    summary_rowid_stride=50,
    summary_float_limit=50,
    sample_data_rowid_stride=20,
    sample_data_points_per_grid_cell=2,
    float_profile_downsample_threshold=15_000,
    validation_issue_preview_limit=3,
    db_insert_chunk_size=100_000,
    db_insert_batch_size=5_000,
    db_insert_large_dataset_threshold=50_000,
    test_dataset_total_rows=10_000,
    test_dataset_float_rows=5_000,
    test_insert_chunk_size=3_000,
    test_insert_batch_size=1_000,
    sample_profile_rate_thresholds=((50_000, 20), (25_000, 10), (10_000, 5)),
)


MEDIUM_TEST = DataConfig(
    name="MEDIUM_TEST",
    max_files=4,
    chunk_size=10_000,
    max_profiles_per_file=500,
    db_sample_limit=10_000,
    dataframe_sample_limit=10_000,
    float_profile_sample_limit=10_000,
    float_profile_bin_count=50,
    float_profile_sample_per_bin=10,
    query_example_limit=5,
    top_float_display_limit=5,
    db_stats_primary_rowid_stride=1_000,
    db_stats_primary_sample_limit=1_000,
    db_stats_fallback_rowid_stride=100,
    db_stats_fallback_sample_limit=10_000,
    summary_rowid_stride=50,
    summary_float_limit=100,
    sample_data_rowid_stride=20,
    sample_data_points_per_grid_cell=2,
    float_profile_downsample_threshold=15_000,
    validation_issue_preview_limit=3,
    db_insert_chunk_size=100_000,
    db_insert_batch_size=5_000,
    db_insert_large_dataset_threshold=50_000,
    test_dataset_total_rows=10_000,
    test_dataset_float_rows=5_000,
    test_insert_chunk_size=3_000,
    test_insert_batch_size=1_000,
    sample_profile_rate_thresholds=((50_000, 20), (25_000, 10), (10_000, 5)),
)


LARGE_TEST = DataConfig(
    name="LARGE_TEST",
    max_files=20,
    chunk_size=10_000,
    max_profiles_per_file=5_000,
    db_sample_limit=50_000,
    dataframe_sample_limit=50_000,
    float_profile_sample_limit=15_000,
    float_profile_bin_count=50,
    float_profile_sample_per_bin=10,
    query_example_limit=5,
    top_float_display_limit=5,
    db_stats_primary_rowid_stride=1_000,
    db_stats_primary_sample_limit=1_000,
    db_stats_fallback_rowid_stride=100,
    db_stats_fallback_sample_limit=10_000,
    summary_rowid_stride=50,
    summary_float_limit=100,
    sample_data_rowid_stride=20,
    sample_data_points_per_grid_cell=2,
    float_profile_downsample_threshold=15_000,
    validation_issue_preview_limit=3,
    db_insert_chunk_size=100_000,
    db_insert_batch_size=5_000,
    db_insert_large_dataset_threshold=50_000,
    test_dataset_total_rows=10_000,
    test_dataset_float_rows=5_000,
    test_insert_chunk_size=3_000,
    test_insert_batch_size=1_000,
    sample_profile_rate_thresholds=((50_000, 20), (25_000, 10), (10_000, 5)),
)


PRESETS: Dict[str, DataConfig] = {
    "SMALL_TEST": SMALL_TEST,
    "MEDIUM_TEST": MEDIUM_TEST,
    "LARGE_TEST": LARGE_TEST,
}


ACTIVE_PRESET_NAME = os.getenv("FLOATCHAT_DATA_PRESET", "MEDIUM_TEST").upper()
ACTIVE_DATA_CONFIG = PRESETS.get(ACTIVE_PRESET_NAME, MEDIUM_TEST)


def log_active_config() -> DataConfig:
    """Log the active preset and its values for debugging."""
    print(f"Active data preset: {ACTIVE_DATA_CONFIG.name}")
    logger.info("Active data preset: %s", ACTIVE_DATA_CONFIG.name)
    for key, value in asdict(ACTIVE_DATA_CONFIG).items():
        print(f"{key}={value}")
        logger.info("%s=%s", key, value)
    return ACTIVE_DATA_CONFIG


def get_float_profile_sample_rate(record_count: int) -> int:
    """Return the sampling rate used to thin very large float profiles."""
    for threshold, sample_rate in ACTIVE_DATA_CONFIG.sample_profile_rate_thresholds:
        if record_count > threshold:
            return sample_rate
    return 1


# Flat aliases keep the rest of the codebase easy to read and backward compatible.
MAX_FILES = ACTIVE_DATA_CONFIG.max_files
CHUNK_SIZE = ACTIVE_DATA_CONFIG.chunk_size
MAX_PROFILES_PER_FILE = ACTIVE_DATA_CONFIG.max_profiles_per_file
DB_SAMPLE_LIMIT = ACTIVE_DATA_CONFIG.db_sample_limit
DATAFRAME_SAMPLE_LIMIT = ACTIVE_DATA_CONFIG.dataframe_sample_limit
FLOAT_PROFILE_SAMPLE_LIMIT = ACTIVE_DATA_CONFIG.float_profile_sample_limit
FLOAT_PROFILE_BIN_COUNT = ACTIVE_DATA_CONFIG.float_profile_bin_count
FLOAT_PROFILE_SAMPLE_PER_BIN = ACTIVE_DATA_CONFIG.float_profile_sample_per_bin
QUERY_EXAMPLE_LIMIT = ACTIVE_DATA_CONFIG.query_example_limit
TOP_FLOAT_DISPLAY_LIMIT = ACTIVE_DATA_CONFIG.top_float_display_limit
DB_STATS_PRIMARY_ROWID_STRIDE = ACTIVE_DATA_CONFIG.db_stats_primary_rowid_stride
DB_STATS_PRIMARY_SAMPLE_LIMIT = ACTIVE_DATA_CONFIG.db_stats_primary_sample_limit
DB_STATS_FALLBACK_ROWID_STRIDE = ACTIVE_DATA_CONFIG.db_stats_fallback_rowid_stride
DB_STATS_FALLBACK_SAMPLE_LIMIT = ACTIVE_DATA_CONFIG.db_stats_fallback_sample_limit
SUMMARY_ROWID_STRIDE = ACTIVE_DATA_CONFIG.summary_rowid_stride
SUMMARY_FLOAT_LIMIT = ACTIVE_DATA_CONFIG.summary_float_limit
SAMPLE_DATA_ROWID_STRIDE = ACTIVE_DATA_CONFIG.sample_data_rowid_stride
SAMPLE_DATA_POINTS_PER_GRID_CELL = ACTIVE_DATA_CONFIG.sample_data_points_per_grid_cell
FLOAT_PROFILE_DOWNSAMPLE_THRESHOLD = ACTIVE_DATA_CONFIG.float_profile_downsample_threshold
VALIDATION_ISSUE_PREVIEW_LIMIT = ACTIVE_DATA_CONFIG.validation_issue_preview_limit
DB_INSERT_CHUNK_SIZE = ACTIVE_DATA_CONFIG.db_insert_chunk_size
DB_INSERT_BATCH_SIZE = ACTIVE_DATA_CONFIG.db_insert_batch_size
DB_INSERT_LARGE_DATASET_THRESHOLD = ACTIVE_DATA_CONFIG.db_insert_large_dataset_threshold
TEST_DATASET_TOTAL_ROWS = ACTIVE_DATA_CONFIG.test_dataset_total_rows
TEST_DATASET_FLOAT_ROWS = ACTIVE_DATA_CONFIG.test_dataset_float_rows
TEST_INSERT_CHUNK_SIZE = ACTIVE_DATA_CONFIG.test_insert_chunk_size
TEST_INSERT_BATCH_SIZE = ACTIVE_DATA_CONFIG.test_insert_batch_size


# =========================================================
# DIVERSE FLOAT SAMPLING
# =========================================================
# Enable diverse sampling to get multiple different floats in ingestion
DIVERSE_FLOAT_SAMPLING = True
# Max files to select from each float (limits duplication)
MAX_FILES_PER_FLOAT = 3

