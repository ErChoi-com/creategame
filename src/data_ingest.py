"""
Data Ingestion Module for Binance Historical Data

Fetches historical OHLCV data from Binance with retry logic and rate limiting.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Fetch historical kline data from Binance API with retry and rate limiting."""

    BASE_URL = "https://api.binance.com/api/v3"

    def __init__(self, config: Dict):
        """
        Initialize the data fetcher.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.data_config = config["data"]
        self.api_config = self.data_config["api"]
        self.session = self._create_session()
        self.rate_limit_delay = 60.0 / self.api_config["rate_limit_per_minute"]

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
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Fetch all historical data for a symbol between start and end dates.

        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with OHLCV data
        """
        logger.info(
            f"Fetching {symbol} data from {start_date.date()} to {end_date.date()}"
        )

        interval = self.data_config["interval"]
        all_klines = []

        # Convert to milliseconds
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        # Binance limits to 1000 records per request
        # For 1m interval, 1000 minutes ≈ 16.7 hours
        limit = 1000
        current_start = start_ms

        while current_start < end_ms:
            try:
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

                logger.debug(
                    f"Fetched {len(klines)} klines, total: {len(all_klines)}"
                )

                # Check if we've reached the end
                if len(klines) < limit:
                    break

            except Exception as e:
                logger.error(f"Error during fetch loop: {e}")
                raise

        # Convert to DataFrame
        df = self._klines_to_dataframe(all_klines)
        logger.info(f"Fetched {len(df)} records for {symbol}")

        return df

    def _klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        Convert raw klines data to a pandas DataFrame.

        Args:
            klines: List of klines from Binance API

        Returns:
            DataFrame with processed OHLCV data
        """
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
        df = df.drop_duplicates(subset=["open_time"], keep="first")

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
