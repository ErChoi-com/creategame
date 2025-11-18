"""
Data Ingestion Module for Binance Historical Data

Fetches historical OHLCV data from Binance with retry logic and rate limiting.
Enhanced with type hints, validation, and progress tracking.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

try:
    from utils import (
        validate_dataframe,
        check_data_quality,
        print_header,
        print_section,
        format_number,
        ensure_directory,
    )
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    # Fallback implementations
    def ensure_directory(path):
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    def format_number(num, decimals=2):
        return f"{num:,.{decimals}f}"
    def print_header(text, char="=", width=60):
        print(f"\n{char * width}\n{text.center(width)}\n{char * width}\n")
    def print_section(text, char="-", width=60):
        print(f"\n{text}\n{char * width}")
    def validate_dataframe(df, required_columns, min_rows=0, check_nulls=True):
        if df is None or len(df) == 0:
            return False, "DataFrame is empty"
        missing = set(required_columns) - set(df.columns)
        if missing:
            return False, f"Missing columns: {missing}"
        return True, "Valid"
    def check_data_quality(df, column="close"):
        return {"null_count": df[column].isna().sum(), "time_gaps": 0}

logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Fetch historical kline data from Binance API with retry and rate limiting."""

    BASE_URL = "https://api.binance.com/api/v3"
    INTERVALS = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]

    def __init__(self, config: Dict):
        """
        Initialize the data fetcher.

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        self.data_config = config["data"]
        self.api_config = self.data_config["api"]

        # Validate configuration
        self._validate_config()

        self.session = self._create_session()
        self.rate_limit_delay = 60.0 / self.api_config["rate_limit_per_minute"]
        self.last_request_time = 0

    def _validate_config(self) -> None:
        """Validate data configuration."""
        if not self.data_config.get("symbols"):
            raise ValueError("No symbols specified in data configuration")

        interval = self.data_config.get("interval", "1m")
        if interval not in self.INTERVALS:
            raise ValueError(f"Invalid interval: {interval}. Must be one of {self.INTERVALS}")

        if self.data_config.get("lookback_days", 0) <= 0:
            raise ValueError("lookback_days must be positive")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()

        retry_strategy = Retry(
            total=self.api_config["max_retries"],
            backoff_factor=self.api_config["retry_backoff_factor"],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        limit: int = 1000,
    ) -> List[List]:
        """
        Fetch klines (candlestick) data from Binance.

        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1m', '5m', '1h')
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of klines to fetch per request (max 1000)

        Returns:
            List of klines
        """
        endpoint = f"{self.BASE_URL}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit,
        }

        try:
            time.sleep(self.rate_limit_delay)  # Rate limiting
            response = self.session.get(
                endpoint, params=params, timeout=self.api_config["timeout_seconds"]
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            raise

    def fetch_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime, show_progress: bool = True
    ) -> pd.DataFrame:
        """
        Fetch all historical data for a symbol between start and end dates.

        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            show_progress: Whether to show progress bar

        Returns:
            DataFrame with OHLCV data

        Raises:
            ValueError: If date range is invalid
            requests.exceptions.RequestException: If API request fails
        """
        if start_date >= end_date:
            raise ValueError("start_date must be before end_date")

        logger.info(f"Fetching {symbol} data from {start_date.date()} to {end_date.date()}")

        interval = self.data_config["interval"]
        all_klines = []

        # Convert to milliseconds
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        # Calculate total number of requests needed (approximate)
        interval_ms = self._interval_to_milliseconds(interval)
        total_bars = (end_ms - start_ms) // interval_ms
        total_requests = int(np.ceil(total_bars / 1000))

        # Binance limits to 1000 records per request
        limit = 1000
        current_start = start_ms

        # Progress bar
        if HAS_TQDM and show_progress:
            pbar = tqdm(
                total=total_requests,
                desc=f"Fetching {symbol}",
                unit="req",
            )
        else:
            pbar = None

        try:
            while current_start < end_ms:
                klines = self.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=end_ms,
                    limit=limit,
                )

                if not klines:
                    logger.warning(f"No data returned for {symbol} at {current_start}")
                    break

                all_klines.extend(klines)

                # Update start time to the last kline's close time + 1ms
                current_start = klines[-1][6] + 1

                if pbar:
                    pbar.update(1)

                # Check if we've reached the end
                if len(klines) < limit:
                    break

        finally:
            if pbar:
                pbar.close()

        # Convert to DataFrame
        df = self._klines_to_dataframe(all_klines)
        logger.info(f"Fetched {format_number(len(df), 0)} records for {symbol}")

        # Validate data quality
        if HAS_UTILS:
            quality = check_data_quality(df)
            if quality["null_count"] > 0:
                logger.warning(f"Found {quality['null_count']} null values in close prices")
            if quality.get("time_gaps", 0) > 0:
                logger.warning(f"Found {quality['time_gaps']} gaps in time series")

        return df

    def _interval_to_milliseconds(self, interval: str) -> int:
        """
        Convert interval string to milliseconds.

        Args:
            interval: Interval string (e.g., '1m', '1h', '1d')

        Returns:
            Interval in milliseconds
        """
        unit = interval[-1]
        value = int(interval[:-1])

        if unit == 'm':
            return value * 60 * 1000
        elif unit == 'h':
            return value * 60 * 60 * 1000
        elif unit == 'd':
            return value * 24 * 60 * 60 * 1000
        else:
            raise ValueError(f"Unknown interval unit: {unit}")

    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        Convert raw klines data to a pandas DataFrame.

        Args:
            klines: List of klines from Binance API

        Returns:
            DataFrame with processed OHLCV data
        """
        if not klines:
            return pd.DataFrame()

        df = pd.DataFrame(
            klines,
            columns=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_volume",
                "trades",
                "taker_buy_base",
                "taker_buy_quote",
                "ignore",
            ],
        )

        # Convert types
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        # Keep only required columns
        df = df[["open_time", "open", "high", "low", "close", "volume"]]

        # Sort by time
        df = df.sort_values("open_time").reset_index(drop=True)

        # Remove duplicates
        duplicates_before = len(df)
        df = df.drop_duplicates(subset=["open_time"], keep="first")
        duplicates_removed = duplicates_before - len(df)

        if duplicates_removed > 0:
            logger.warning(f"Removed {duplicates_removed} duplicate records")

        return df

    def save_data(self, df: pd.DataFrame, symbol: str, output_dir: Path):
        """
        Save DataFrame to disk.

        Args:
            df: DataFrame to save
            symbol: Trading pair symbol
            output_dir: Output directory
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        storage_format = self.data_config["storage_format"]

        if storage_format == "parquet":
            filepath = output_dir / f"{symbol}.parquet"
            df.to_parquet(filepath, index=False, compression="snappy")
        elif storage_format == "csv":
            filepath = output_dir / f"{symbol}.csv"
            df.to_csv(filepath, index=False)
        else:
            raise ValueError(f"Unsupported storage format: {storage_format}")

        logger.info(f"Saved {len(df)} records to {filepath}")

    def load_data(self, symbol: str, data_dir: Path) -> Optional[pd.DataFrame]:
        """
        Load data from disk if it exists.

        Args:
            symbol: Trading pair symbol
            data_dir: Data directory

        Returns:
            DataFrame if file exists, None otherwise
        """
        storage_format = self.data_config["storage_format"]

        if storage_format == "parquet":
            filepath = data_dir / f"{symbol}.parquet"
        elif storage_format == "csv":
            filepath = data_dir / f"{symbol}.csv"
        else:
            raise ValueError(f"Unsupported storage format: {storage_format}")

        if filepath.exists():
            logger.info(f"Loading existing data from {filepath}")
            if storage_format == "parquet":
                df = pd.read_parquet(filepath)
            else:
                df = pd.read_csv(filepath, parse_dates=["open_time"])
            return df
        else:
            return None

    def fetch_and_save(
        self, symbols: List[str], lookback_days: int, force_refresh: bool = False
    ):
        """
        Main entry point: fetch and save data for all symbols.

        Args:
            symbols: List of trading pair symbols
            lookback_days: Number of days to look back
            force_refresh: If True, re-download even if data exists
        """
        data_dir = Path(self.data_config["data_dir"])
        data_dir.mkdir(parents=True, exist_ok=True)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)

        for symbol in symbols:
            logger.info(f"Processing {symbol}")

            if not force_refresh:
                existing_df = self.load_data(symbol, data_dir)
                if existing_df is not None and len(existing_df) > 0:
                    # Check if data is recent enough
                    last_date = pd.to_datetime(existing_df["open_time"].max())
                    if (end_date - last_date).days <= 1:
                        logger.info(
                            f"Data for {symbol} is up-to-date (last: {last_date})"
                        )
                        continue

            # Fetch data
            df = self.fetch_historical_data(symbol, start_date, end_date)

            # Save data
            self.save_data(df, symbol, data_dir)

        logger.info("Data ingestion completed")


def main():
    """Main function for standalone execution."""
    import yaml
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load config
    config_path = Path("configs/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Create fetcher
    fetcher = BinanceDataFetcher(config)

    # Fetch data
    symbols = config["data"]["symbols"]
    lookback_days = config["data"]["lookback_days"]

    fetcher.fetch_and_save(symbols, lookback_days, force_refresh=False)


if __name__ == "__main__":
    main()
