"""
Utility functions for the Kronos crypto prediction system.

Provides common functionality used across modules.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import json
from datetime import datetime
import pandas as pd
import numpy as np


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Setup centralized logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("kronos")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"kronos_{timestamp}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate configuration file.

    Args:
        config_path: Path to config YAML file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Validate config
    validate_config(config)

    return config


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration dictionary.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_keys = ["seed", "data", "labeling", "features", "models", "backtest", "tuning", "reporting"]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")

    # Validate data config
    data_config = config["data"]
    if not data_config.get("symbols"):
        raise ValueError("No symbols specified in data config")

    if data_config.get("lookback_days", 0) <= 0:
        raise ValueError("lookback_days must be positive")

    # Validate labeling config
    label_config = config["labeling"]
    if label_config.get("horizon_minutes", 0) <= 0:
        raise ValueError("horizon_minutes must be positive")

    if label_config.get("threshold_pct", 0) <= 0:
        raise ValueError("threshold_pct must be positive")

    num_classes = label_config.get("num_classes", 3)
    if num_classes not in [2, 3]:
        raise ValueError("num_classes must be 2 or 3")

    # Validate model config
    model_config = config["models"]
    valid_models = ["lightgbm", "xgboost", "random_forest", "catboost"]
    if model_config.get("primary") not in valid_models:
        raise ValueError(f"Invalid model type. Must be one of: {valid_models}")

    # Validate backtest config
    backtest_config = config["backtest"]
    if backtest_config.get("train_months", 0) <= 0:
        raise ValueError("train_months must be positive")

    if backtest_config.get("valid_months", 0) <= 0:
        raise ValueError("valid_months must be positive")


def save_json(data: Dict, filepath: Path) -> None:
    """
    Save dictionary to JSON file.

    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to native Python types
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        return obj

    data_converted = convert_types(data)

    with open(filepath, "w") as f:
        json.dump(data_converted, f, indent=2)


def load_json(filepath: Path) -> Dict:
    """
    Load dictionary from JSON file.

    Args:
        filepath: Input file path

    Returns:
        Dictionary from JSON
    """
    with open(filepath, "r") as f:
        return json.load(f)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 15m 30s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_number(num: float, decimals: int = 2) -> str:
    """
    Format number with thousands separator.

    Args:
        num: Number to format
        decimals: Number of decimal places

    Returns:
        Formatted string
    """
    return f"{num:,.{decimals}f}"


def print_header(text: str, char: str = "=", width: int = 60) -> None:
    """
    Print a formatted header.

    Args:
        text: Header text
        char: Character for border
        width: Total width
    """
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def print_section(text: str, char: str = "-", width: int = 60) -> None:
    """
    Print a formatted section header.

    Args:
        text: Section text
        char: Character for border
        width: Total width
    """
    print("\n" + text)
    print(char * width)


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: list,
    min_rows: int = 0,
    check_nulls: bool = True,
) -> tuple[bool, str]:
    """
    Validate a pandas DataFrame.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        min_rows: Minimum number of rows required
        check_nulls: Whether to check for null values

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if DataFrame is empty
    if df is None or len(df) == 0:
        return False, "DataFrame is empty"

    # Check minimum rows
    if len(df) < min_rows:
        return False, f"DataFrame has {len(df)} rows, minimum {min_rows} required"

    # Check required columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        return False, f"Missing required columns: {missing_cols}"

    # Check for null values
    if check_nulls:
        null_cols = df[required_columns].columns[df[required_columns].isna().any()].tolist()
        if null_cols:
            return False, f"Null values found in columns: {null_cols}"

    return True, "Valid"


def estimate_memory_usage(df: pd.DataFrame) -> str:
    """
    Estimate memory usage of a DataFrame.

    Args:
        df: DataFrame to analyze

    Returns:
        Formatted memory usage string
    """
    memory_bytes = df.memory_usage(deep=True).sum()
    memory_mb = memory_bytes / (1024 ** 2)

    if memory_mb < 1024:
        return f"{memory_mb:.2f} MB"
    else:
        memory_gb = memory_mb / 1024
        return f"{memory_gb:.2f} GB"


def check_data_quality(df: pd.DataFrame, column: str = "close") -> Dict[str, Any]:
    """
    Check data quality metrics.

    Args:
        df: DataFrame to analyze
        column: Column to analyze

    Returns:
        Dictionary with quality metrics
    """
    quality = {
        "total_rows": len(df),
        "null_count": df[column].isna().sum(),
        "null_pct": df[column].isna().mean() * 100,
        "zero_count": (df[column] == 0).sum(),
        "zero_pct": (df[column] == 0).mean() * 100,
        "unique_count": df[column].nunique(),
    }

    # Check for duplicates in time column if it exists
    if "open_time" in df.columns:
        quality["duplicate_timestamps"] = df["open_time"].duplicated().sum()

    # Check for gaps in time series
    if "open_time" in df.columns:
        time_diffs = df["open_time"].diff()
        expected_diff = time_diffs.mode()[0] if len(time_diffs.mode()) > 0 else pd.Timedelta(minutes=1)
        gaps = (time_diffs > expected_diff * 1.5).sum()
        quality["time_gaps"] = gaps

    return quality


def create_summary_table(data: Dict[str, Dict[str, float]], title: str = "Summary") -> str:
    """
    Create a formatted summary table.

    Args:
        data: Dictionary of {row_name: {col_name: value}}
        title: Table title

    Returns:
        Formatted table string
    """
    lines = [f"\n{title}", "=" * 60]

    # Get all column names
    all_cols = set()
    for row_data in data.values():
        all_cols.update(row_data.keys())

    all_cols = sorted(all_cols)

    # Create header
    header = f"{'Metric':<30}"
    for col in all_cols:
        header += f"{col:>12}"
    lines.append(header)
    lines.append("-" * 60)

    # Create rows
    for row_name, row_data in data.items():
        row = f"{row_name:<30}"
        for col in all_cols:
            value = row_data.get(col, 0)
            if isinstance(value, float):
                row += f"{value:>12.4f}"
            else:
                row += f"{value:>12}"
        lines.append(row)

    return "\n".join(lines)


class ProgressTracker:
    """Track progress of long-running operations."""

    def __init__(self, total: int, desc: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total: Total number of items
            desc: Description of the operation
        """
        self.total = total
        self.desc = desc
        self.current = 0
        self.start_time = datetime.now()

    def update(self, n: int = 1) -> None:
        """
        Update progress.

        Args:
            n: Number of items processed
        """
        self.current += n
        self._print_progress()

    def _print_progress(self) -> None:
        """Print progress bar."""
        pct = (self.current / self.total) * 100 if self.total > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Estimate time remaining
        if self.current > 0:
            eta_seconds = (elapsed / self.current) * (self.total - self.current)
            eta_str = format_duration(eta_seconds)
        else:
            eta_str = "unknown"

        # Create progress bar
        bar_length = 30
        filled = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\r{self.desc}: [{bar}] {pct:.1f}% | {self.current}/{self.total} | ETA: {eta_str}", end="", flush=True)

        if self.current >= self.total:
            print()  # New line when complete


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if needed.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path
