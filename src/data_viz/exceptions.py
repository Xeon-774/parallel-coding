"""Custom exception classes for data visualization platform."""


class DataVizError(Exception):
    """Base exception class for all data visualization errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DataLoadError(DataVizError):
    """Exception raised when data loading fails."""

    def __init__(self, message: str, file_path: str = None, details: dict = None):
        details = details or {}
        if file_path:
            details["file_path"] = file_path
        super().__init__(message, details)


class FileNotFoundError(DataLoadError):
    """Exception raised when a file is not found."""

    def __init__(self, file_path: str):
        super().__init__(f"File not found: {file_path}", file_path=file_path)


class UnsupportedFileFormatError(DataLoadError):
    """Exception raised when file format is not supported."""

    def __init__(self, file_format: str, supported_formats: list = None):
        details = {"file_format": file_format}
        if supported_formats:
            details["supported_formats"] = supported_formats
        super().__init__(f"Unsupported file format: {file_format}", details=details)


class ValidationError(DataVizError):
    """Exception raised when data validation fails."""

    def __init__(self, message: str, field: str = None, value=None, details: dict = None):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)


class DataTypeError(ValidationError):
    """Exception raised when data type is incorrect."""

    def __init__(self, expected_type: str, actual_type: str, field: str = None):
        super().__init__(
            f"Expected type {expected_type}, got {actual_type}",
            field=field,
            details={"expected_type": expected_type, "actual_type": actual_type},
        )


class MissingColumnError(ValidationError):
    """Exception raised when required column is missing."""

    def __init__(self, column_name: str, available_columns: list = None):
        details = {"missing_column": column_name}
        if available_columns:
            details["available_columns"] = available_columns
        super().__init__(
            f"Missing required column: {column_name}", field=column_name, details=details
        )


class EmptyDataError(ValidationError):
    """Exception raised when data is empty."""

    def __init__(self, message: str = "Data is empty"):
        super().__init__(message)


class ProcessingError(DataVizError):
    """Exception raised when data processing fails."""

    def __init__(self, message: str, operation: str = None, details: dict = None):
        details = details or {}
        if operation:
            details["operation"] = operation
        super().__init__(message, details)


class TransformationError(ProcessingError):
    """Exception raised when data transformation fails."""

    def __init__(self, message: str, transformation: str = None):
        super().__init__(
            message, operation=transformation, details={"transformation_type": transformation}
        )


class AggregationError(ProcessingError):
    """Exception raised when data aggregation fails."""

    def __init__(self, message: str, aggregation_func: str = None):
        super().__init__(
            message, operation=aggregation_func, details={"aggregation_function": aggregation_func}
        )


class VisualizationError(DataVizError):
    """Exception raised when visualization creation fails."""

    def __init__(self, message: str, chart_type: str = None, details: dict = None):
        details = details or {}
        if chart_type:
            details["chart_type"] = chart_type
        super().__init__(message, details)


class InvalidChartTypeError(VisualizationError):
    """Exception raised when chart type is invalid."""

    def __init__(self, chart_type: str, supported_types: list = None):
        details = {"chart_type": chart_type}
        if supported_types:
            details["supported_types"] = supported_types
        super().__init__(
            f"Invalid chart type: {chart_type}", chart_type=chart_type, details=details
        )


class PlottingError(VisualizationError):
    """Exception raised when plotting operation fails."""

    def __init__(self, message: str, chart_type: str = None):
        super().__init__(message, chart_type=chart_type)


class ConfigurationError(DataVizError):
    """Exception raised when configuration is invalid."""

    def __init__(self, message: str, config_key: str = None, details: dict = None):
        details = details or {}
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, details)


class ExportError(DataVizError):
    """Exception raised when export operation fails."""

    def __init__(self, message: str, output_path: str = None, format: str = None):
        details = {}
        if output_path:
            details["output_path"] = output_path
        if format:
            details["format"] = format
        super().__init__(message, details)


class DashboardError(DataVizError):
    """Exception raised when dashboard operation fails."""

    def __init__(self, message: str, component: str = None, details: dict = None):
        details = details or {}
        if component:
            details["component"] = component
        super().__init__(message, details)


class CacheError(DataVizError):
    """Exception raised when cache operation fails."""

    def __init__(self, message: str, cache_key: str = None):
        super().__init__(message, details={"cache_key": cache_key} if cache_key else None)


class MemoryError(DataVizError):
    """Exception raised when memory limit is exceeded."""

    def __init__(
        self, message: str = "Memory limit exceeded", current_usage: int = None, limit: int = None
    ):
        details = {}
        if current_usage:
            details["current_usage_mb"] = current_usage
        if limit:
            details["limit_mb"] = limit
        super().__init__(message, details)


class APIError(DataVizError):
    """Exception raised when API call fails."""

    def __init__(self, message: str, status_code: int = None, endpoint: str = None):
        details = {}
        if status_code:
            details["status_code"] = status_code
        if endpoint:
            details["endpoint"] = endpoint
        super().__init__(message, details)
