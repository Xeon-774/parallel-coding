"""Configuration constants for data visualization platform."""

from typing import Dict, List, Tuple

# Default figure sizes
DEFAULT_FIGURE_SIZE: Tuple[int, int] = (10, 6)
LARGE_FIGURE_SIZE: Tuple[int, int] = (14, 8)
SMALL_FIGURE_SIZE: Tuple[int, int] = (8, 5)
DASHBOARD_FIGURE_SIZE: Tuple[int, int] = (12, 8)

# Color palettes
DEFAULT_COLOR_PALETTE: List[str] = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#7f7f7",
    "#bcbd22",
    "#17becf",
]

CATEGORICAL_COLORS: Dict[str, str] = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#ff9800",
    "info": "#17bec",
}

SEABORN_PALETTE: str = "husl"
MATPLOTLIB_STYLE: str = "seaborn - v0_8 - darkgrid"

# Font settings
DEFAULT_FONT_SIZE: int = 12
TITLE_FONT_SIZE: int = 16
LABEL_FONT_SIZE: int = 12
LEGEND_FONT_SIZE: int = 10
TICK_FONT_SIZE: int = 10

FONT_FAMILY: str = "sans - seri"
FONT_WEIGHT: str = "normal"

# DPI settings
DEFAULT_DPI: int = 100
HIGH_DPI: int = 300
SCREEN_DPI: int = 96

# File formats
SUPPORTED_IMAGE_FORMATS: List[str] = ["png", "jpg", "jpeg", "svg", "pd"]
DEFAULT_IMAGE_FORMAT: str = "png"
SUPPORTED_DATA_FORMATS: List[str] = ["csv", "json", "xlsx", "parquet"]

# Data processing
MAX_ROWS_DISPLAY: int = 100
MAX_COLUMNS_DISPLAY: int = 20
MISSING_VALUE_THRESHOLD: float = 0.5
OUTLIER_STD_THRESHOLD: float = 3.0

# Visualization types
CHART_TYPES: List[str] = [
    "line",
    "bar",
    "scatter",
    "histogram",
    "box",
    "violin",
    "heatmap",
    "pie",
    "area",
    "density",
    "hexbin",
]

# Dashboard settings
DASHBOARD_REFRESH_RATE: int = 5  # seconds
MAX_DASHBOARD_WIDGETS: int = 12
DASHBOARD_GRID_COLS: int = 3
DASHBOARD_GRID_ROWS: int = 4

# Export settings
EXPORT_QUALITY: int = 95
EXPORT_BBOX_INCHES: str = "tight"
EXPORT_PAD_INCHES: float = 0.1

# Logging
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# Cache settings
ENABLE_CACHE: bool = True
CACHE_MAX_SIZE: int = 1000
CACHE_TTL: int = 3600  # seconds

# Plot customization defaults
DEFAULT_ALPHA: float = 0.8
DEFAULT_LINE_WIDTH: float = 2.0
DEFAULT_MARKER_SIZE: float = 50.0
DEFAULT_GRID_ALPHA: float = 0.3

# Statistics
CONFIDENCE_LEVEL: float = 0.95
CORRELATION_METHOD: str = "pearson"  # pearson, spearman, kendall

# Performance
CHUNK_SIZE: int = 10000
MAX_MEMORY_MB: int = 1024
PARALLEL_PROCESSING: bool = True
MAX_WORKERS: int = 4

# Validation
MIN_DATAFRAME_ROWS: int = 1
MIN_DATAFRAME_COLS: int = 1
MAX_FILE_SIZE_MB: int = 500

# API settings
API_TIMEOUT: int = 30  # seconds
MAX_RETRIES: int = 3
RETRY_DELAY: int = 1  # seconds
