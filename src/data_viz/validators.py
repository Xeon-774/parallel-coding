"""Common validation functions for data visualization platform."""

import os
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np
import pandas as pd

from .config import (
    CHART_TYPES,
    MAX_FILE_SIZE_MB,
    MAX_MEMORY_MB,
    MIN_DATAFRAME_COLS,
    MIN_DATAFRAME_ROWS,
    SUPPORTED_DATA_FORMATS,
    SUPPORTED_IMAGE_FORMATS,
)
from .exceptions import (
    DataTypeError,
    EmptyDataError,
    FileNotFoundError,
)
from .exceptions import MemoryError as DataVizMemoryError
from .exceptions import (
    MissingColumnError,
    UnsupportedFileFormatError,
    ValidationError,
)


def validate_file_exists(file_path: Union[str, Path]) -> Path:
    """
    Validate that a file exists.

    Args:
        file_path: Path to the file

    Returns:
        Path object of the validated file

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(str(path))
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {path}")
    return path


def validate_directory_exists(dir_path: Union[str, Path]) -> Path:
    """
    Validate that a directory exists.

    Args:
        dir_path: Path to the directory

    Returns:
        Path object of the validated directory

    Raises:
        ValidationError: If directory does not exist
    """
    path = Path(dir_path)
    if not path.exists():
        raise ValidationError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")
    return path


def validate_file_format(
    file_path: Union[str, Path], allowed_formats: Optional[List[str]] = None
) -> str:
    """
    Validate file format is supported.

    Args:
        file_path: Path to the file
        allowed_formats: List of allowed formats (without dot)

    Returns:
        File extension without dot

    Raises:
        UnsupportedFileFormatError: If format is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower().lstrip(".")

    if allowed_formats is None:
        allowed_formats = SUPPORTED_DATA_FORMATS

    if extension not in allowed_formats:
        raise UnsupportedFileFormatError(extension, allowed_formats)

    return extension


def validate_file_size(file_path: Union[str, Path], max_size_mb: Optional[int] = None) -> int:
    """
    Validate file size is within limits.

    Args:
        file_path: Path to the file
        max_size_mb: Maximum file size in MB

    Returns:
        File size in bytes

    Raises:
        ValidationError: If file is too large
    """
    path = validate_file_exists(file_path)
    file_size = path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    max_size = max_size_mb or MAX_FILE_SIZE_MB

    if file_size_mb > max_size:
        raise ValidationError(
            f"File size ({file_size_mb:.2f}MB) exceeds maximum ({max_size}MB)",
            details={"file_size_mb": file_size_mb, "max_size_mb": max_size},
        )

    return file_size


def validate_dataframe(
    df: pd.DataFrame,
    min_rows: Optional[int] = None,
    min_cols: Optional[int] = None,
    required_columns: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Validate DataFrame meets requirements.

    Args:
        df: DataFrame to validate
        min_rows: Minimum number of rows required
        min_cols: Minimum number of columns required
        required_columns: List of required column names

    Returns:
        Validated DataFrame

    Raises:
        EmptyDataError: If DataFrame is empty
        ValidationError: If DataFrame doesn't meet requirements
    """
    if not isinstance(df, pd.DataFrame):
        raise DataTypeError("pandas.DataFrame", type(df).__name__)

    if df.empty:
        raise EmptyDataError("DataFrame is empty")

    min_rows = min_rows or MIN_DATAFRAME_ROWS
    min_cols = min_cols or MIN_DATAFRAME_COLS

    if len(df) < min_rows:
        raise ValidationError(
            f"DataFrame has {len(df)} rows, minimum required is {min_rows}",
            details={"actual_rows": len(df), "min_rows": min_rows},
        )

    if len(df.columns) < min_cols:
        raise ValidationError(
            f"DataFrame has {len(df.columns)} columns, minimum required is {min_cols}",
            details={"actual_cols": len(df.columns), "min_cols": min_cols},
        )

    if required_columns:
        validate_columns_exist(df, required_columns)

    return df


def validate_columns_exist(df: pd.DataFrame, columns: List[str]) -> None:
    """
    Validate that specified columns exist in DataFrame.

    Args:
        df: DataFrame to check
        columns: List of required column names

    Raises:
        MissingColumnError: If any required column is missing
    """
    missing_columns = [col for col in columns if col not in df.columns]

    if missing_columns:
        raise MissingColumnError(missing_columns[0], available_columns=list(df.columns))


def validate_column_type(
    df: pd.DataFrame, column: str, expected_types: Union[type, List[type]]
) -> None:
    """
    Validate column data type.

    Args:
        df: DataFrame containing the column
        column: Column name to validate
        expected_types: Expected data type(s)

    Raises:
        MissingColumnError: If column doesn't exist
        DataTypeError: If column type is incorrect
    """
    validate_columns_exist(df, [column])

    if not isinstance(expected_types, list):
        expected_types = [expected_types]

    actual_dtype = df[column].dtype

    type_mapping = {
        int: [np.int8, np.int16, np.int32, np.int64],
        float: [np.float16, np.float32, np.float64],
        str: [object],
        bool: [bool],
    }

    valid = False
    for expected_type in expected_types:
        if expected_type in type_mapping:
            if actual_dtype in type_mapping[expected_type]:
                valid = True
                break
        elif actual_dtype == expected_type:
            valid = True
            break

    if not valid:
        expected_str = " or ".join([str(t) for t in expected_types])
        raise DataTypeError(expected_str, str(actual_dtype), field=column)


def validate_numeric_column(df: pd.DataFrame, column: str) -> None:
    """
    Validate that column contains numeric data.

    Args:
        df: DataFrame containing the column
        column: Column name to validate

    Raises:
        ValidationError: If column is not numeric
    """
    validate_columns_exist(df, [column])

    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValidationError(
            f"Column '{column}' must be numeric",
            field=column,
            details={"dtype": str(df[column].dtype)},
        )


def validate_categorical_column(
    df: pd.DataFrame, column: str, max_categories: Optional[int] = None
) -> None:
    """
    Validate that column is suitable for categorical analysis.

    Args:
        df: DataFrame containing the column
        column: Column name to validate
        max_categories: Maximum number of unique values allowed

    Raises:
        ValidationError: If column has too many categories
    """
    validate_columns_exist(df, [column])

    n_unique = df[column].nunique()

    if max_categories and n_unique > max_categories:
        raise ValidationError(
            f"Column '{column}' has {n_unique} unique values, maximum allowed is {max_categories}",
            field=column,
            details={"n_unique": n_unique, "max_categories": max_categories},
        )


def validate_not_empty(value: Any, name: str = "value") -> None:
    """
    Validate that value is not empty.

    Args:
        value: Value to check
        name: Name of the value for error message

    Raises:
        EmptyDataError: If value is empty
    """
    if value is None:
        raise EmptyDataError(f"{name} cannot be None")

    if isinstance(value, (str, list, dict, pd.DataFrame)) and len(value) == 0:
        raise EmptyDataError(f"{name} cannot be empty")


def validate_positive_number(value: Union[int, float], name: str = "value") -> None:
    """
    Validate that number is positive.

    Args:
        value: Number to validate
        name: Name of the value for error message

    Raises:
        ValidationError: If number is not positive
    """
    if not isinstance(value, (int, float)):
        raise DataTypeError("int or float", type(value).__name__)

    if value <= 0:
        raise ValidationError(f"{name} must be positive, got {value}", field=name, value=value)


def validate_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
    name: str = "value",
) -> None:
    """
    Validate that value is within range.

    Args:
        value: Value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        name: Name of the value for error message

    Raises:
        ValidationError: If value is out of range
    """
    if not isinstance(value, (int, float)):
        raise DataTypeError("int or float", type(value).__name__)

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{name} must be >= {min_value}, got {value}", field=name, value=value
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{name} must be <= {max_value}, got {value}", field=name, value=value
        )


def validate_chart_type(chart_type: str) -> None:
    """
    Validate that chart type is supported.

    Args:
        chart_type: Chart type to validate

    Raises:
        ValidationError: If chart type is not supported
    """
    if chart_type not in CHART_TYPES:
        raise ValidationError(
            f"Unsupported chart type: {chart_type}",
            field="chart_type",
            value=chart_type,
            details={"supported_types": CHART_TYPES},
        )


def validate_image_format(format: str) -> None:
    """
    Validate that image format is supported.

    Args:
        format: Image format to validate

    Raises:
        UnsupportedFileFormatError: If format is not supported
    """
    format_lower = format.lower().lstrip(".")
    if format_lower not in SUPPORTED_IMAGE_FORMATS:
        raise UnsupportedFileFormatError(format_lower, SUPPORTED_IMAGE_FORMATS)


def validate_memory_usage(size_bytes: int, max_mb: Optional[int] = None) -> None:
    """
    Validate that memory usage is within limits.

    Args:
        size_bytes: Memory size in bytes
        max_mb: Maximum memory in MB

    Raises:
        MemoryError: If memory usage exceeds limit
    """
    size_mb = size_bytes / (1024 * 1024)
    max_size = max_mb or MAX_MEMORY_MB

    if size_mb > max_size:
        raise DataVizMemoryError(
            f"Memory usage ({size_mb:.2f}MB) exceeds limit ({max_size}MB)",
            current_usage=int(size_mb),
            limit=max_size,
        )


def validate_output_path(output_path: Union[str, Path], create_dirs: bool = True) -> Path:
    """
    Validate and prepare output path.

    Args:
        output_path: Output file path
        create_dirs: Whether to create parent directories if they don't exist

    Returns:
        Path object of the validated output path

    Raises:
        ValidationError: If path is invalid
    """
    path = Path(output_path)

    if path.exists() and path.is_dir():
        raise ValidationError(f"Output path is a directory: {path}")

    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.parent.exists():
        raise ValidationError(f"Parent directory does not exist: {path.parent}")

    return path


def validate_color(color: str) -> None:
    """
    Validate color format.

    Args:
        color: Color string to validate

    Raises:
        ValidationError: If color format is invalid
    """
    import re

    # Check if hex color
    hex_pattern = r"^#(?:[0-9a-fA-F]{3}){1,2}$"
    if re.match(hex_pattern, color):
        return

    # Check if named color (basic validation)
    named_colors = {
        "red",
        "blue",
        "green",
        "yellow",
        "black",
        "white",
        "gray",
        "cyan",
        "magenta",
        "orange",
        "purple",
        "brown",
        "pink",
    }
    if color.lower() in named_colors:
        return

    # Check if rgb/rgba format
    rgb_pattern = r"^rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(?:,\s*[\d.]+\s*)?\)$"
    if re.match(rgb_pattern, color):
        return

    raise ValidationError(f"Invalid color format: {color}", field="color", value=color)
