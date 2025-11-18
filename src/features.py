"""
Feature Engineering Module for Crypto Price Prediction

Generates technical indicators and features from OHLCV data.
"""

import logging
from typing import Dict, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FeatureGenerator:
    """Generate technical features from OHLCV data."""

    def __init__(self, config: Dict):
        """
        Initialize the feature generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.feature_config = config["features"]

    def generate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate all configured features.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added feature columns
        """
        df = df.copy()

        logger.info("Generating features...")

        # Price-based features
        df = self._add_log_returns(df)
        df = self._add_rolling_stats(df)
        df = self._add_z_scores(df)

        # Volatility features
        df = self._add_atr(df)
        df = self._add_realized_volatility(df)

        # Momentum indicators
        df = self._add_rsi(df)
        df = self._add_macd(df)
        df = self._add_stochastic(df)

        # Volume features
        df = self._add_vwap(df)
        df = self._add_volume_zscore(df)

        # Microstructure features
        df = self._add_microstructure(df)

        # Drop NaN rows created by rolling windows
        initial_len = len(df)
        df = df.dropna()
        logger.info(f"Dropped {initial_len - len(df)} rows with NaN features")

        # Get feature columns (exclude OHLCV and metadata)
        feature_cols = [
            col
            for col in df.columns
            if col
            not in [
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "label",
                "return_10m",
                "future_close",
            ]
        ]
        logger.info(f"Generated {len(feature_cols)} features")

        return df

    def _add_log_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add log returns for various windows."""
        windows = self.feature_config["log_returns"]["windows"]

        for window in windows:
            col_name = f"log_return_{window}m"
            df[col_name] = np.log(df["close"] / df["close"].shift(window))

        return df

    def _add_rolling_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rolling statistics (mean, std, min, max)."""
        windows = self.feature_config["rolling_stats"]["windows"]
        stats = self.feature_config["rolling_stats"]["stats"]

        for window in windows:
            rolling = df["close"].rolling(window=window)

            if "mean" in stats:
                df[f"rolling_mean_{window}m"] = rolling.mean()

            if "std" in stats:
                df[f"rolling_std_{window}m"] = rolling.std()

            if "min" in stats:
                df[f"rolling_min_{window}m"] = rolling.min()

            if "max" in stats:
                df[f"rolling_max_{window}m"] = rolling.max()

        return df

    def _add_z_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add z-scores for price."""
        windows = self.feature_config["z_scores"]["windows"]

        for window in windows:
            rolling_mean = df["close"].rolling(window=window).mean()
            rolling_std = df["close"].rolling(window=window).std()
            df[f"zscore_{window}m"] = (df["close"] - rolling_mean) / rolling_std

        return df

    def _add_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Average True Range (ATR) indicator."""
        windows = self.feature_config["volatility"]["atr_windows"]

        # Calculate True Range
        df["tr1"] = df["high"] - df["low"]
        df["tr2"] = abs(df["high"] - df["close"].shift(1))
        df["tr3"] = abs(df["low"] - df["close"].shift(1))
        df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)

        # Calculate ATR for each window
        for window in windows:
            df[f"atr_{window}m"] = df["true_range"].rolling(window=window).mean()

        # Clean up temporary columns
        df = df.drop(columns=["tr1", "tr2", "tr3", "true_range"])

        return df

    def _add_realized_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add realized volatility."""
        windows = self.feature_config["volatility"]["realized_vol_windows"]

        # Use 1-minute log returns as base
        if "log_return_1m" not in df.columns:
            df["log_return_1m"] = np.log(df["close"] / df["close"].shift(1))

        for window in windows:
            df[f"realized_vol_{window}m"] = (
                df["log_return_1m"].rolling(window=window).std() * np.sqrt(window)
            )

        return df

    def _add_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Relative Strength Index (RSI)."""
        windows = self.feature_config["momentum"]["rsi_windows"]

        # Calculate price changes
        delta = df["close"].diff()

        for window in windows:
            # Separate gains and losses
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # Calculate average gains and losses
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            df[f"rsi_{window}"] = 100 - (100 / (1 + rs))

        return df

    def _add_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Moving Average Convergence Divergence (MACD)."""
        macd_config = self.feature_config["momentum"]["macd"]
        fast = macd_config["fast"]
        slow = macd_config["slow"]
        signal = macd_config["signal"]

        # Calculate EMAs
        ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

        # MACD line
        df["macd"] = ema_fast - ema_slow

        # Signal line
        df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()

        # MACD histogram
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        return df

    def _add_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Stochastic Oscillator."""
        stoch_config = self.feature_config["momentum"]["stochastic"]
        k_window = stoch_config["k_window"]
        d_window = stoch_config["d_window"]

        # Calculate %K
        low_min = df["low"].rolling(window=k_window).min()
        high_max = df["high"].rolling(window=k_window).max()

        df["stoch_k"] = 100 * (df["close"] - low_min) / (high_max - low_min)

        # Calculate %D (moving average of %K)
        df["stoch_d"] = df["stoch_k"].rolling(window=d_window).mean()

        return df

    def _add_vwap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Volume Weighted Average Price (VWAP) delta."""
        windows = self.feature_config["volume"]["vwap_windows"]

        # Calculate typical price
        df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3

        for window in windows:
            # Calculate VWAP
            vwap = (
                (df["typical_price"] * df["volume"]).rolling(window=window).sum()
                / df["volume"].rolling(window=window).sum()
            )

            # Calculate delta from VWAP
            df[f"vwap_delta_{window}m"] = (df["close"] - vwap) / vwap

        # Clean up
        df = df.drop(columns=["typical_price"])

        return df

    def _add_volume_zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume z-scores."""
        windows = self.feature_config["volume"]["volume_zscore_windows"]

        for window in windows:
            rolling_mean = df["volume"].rolling(window=window).mean()
            rolling_std = df["volume"].rolling(window=window).std()
            df[f"volume_zscore_{window}m"] = (
                df["volume"] - rolling_mean
            ) / rolling_std

        return df

    def _add_microstructure(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add microstructure features."""
        micro_config = self.feature_config["microstructure"]

        if micro_config["high_low_range"]:
            df["hl_range"] = (df["high"] - df["low"]) / df["close"]

        if micro_config["close_open_spread"]:
            df["co_spread"] = (df["close"] - df["open"]) / df["open"]

        if micro_config["candle_body_ratio"]:
            # Body size relative to full range
            body = abs(df["close"] - df["open"])
            full_range = df["high"] - df["low"]
            df["body_ratio"] = body / full_range.replace(0, np.nan)

        return df

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of feature column names.

        Args:
            df: DataFrame with features

        Returns:
            List of feature column names
        """
        exclude_cols = [
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "label",
            "return_10m",
            "future_close",
        ]

        feature_cols = [col for col in df.columns if col not in exclude_cols]

        return feature_cols

    def validate_features(self, df: pd.DataFrame) -> bool:
        """
        Validate generated features.

        Args:
            df: DataFrame with features

        Returns:
            True if valid, False otherwise
        """
        # Check for NaN values
        feature_cols = self.get_feature_columns(df)

        if df[feature_cols].isna().any().any():
            nan_cols = df[feature_cols].columns[df[feature_cols].isna().any()].tolist()
            logger.warning(f"Found NaN values in features: {nan_cols}")
            return False

        # Check for infinite values
        if np.isinf(df[feature_cols]).any().any():
            inf_cols = df[feature_cols].columns[np.isinf(df[feature_cols]).any()].tolist()
            logger.warning(f"Found infinite values in features: {inf_cols}")
            return False

        logger.info(f"All {len(feature_cols)} features are valid")
        return True


def main():
    """Main function for standalone testing."""
    import yaml
    from pathlib import Path
    import sys
    from labeling import TrendLabeler

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

    # Load data
    data_dir = Path(config["data"]["data_dir"])
    symbols = config["data"]["symbols"]

    labeler = TrendLabeler(config)
    feature_gen = FeatureGenerator(config)

    for symbol in symbols:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Processing {symbol}")
        logger.info(f"{'=' * 60}")

        # Load data
        storage_format = config["data"]["storage_format"]
        if storage_format == "parquet":
            filepath = data_dir / f"{symbol}.parquet"
            df = pd.read_parquet(filepath)
        else:
            filepath = data_dir / f"{symbol}.csv"
            df = pd.read_csv(filepath, parse_dates=["open_time"])

        logger.info(f"Loaded {len(df)} records")

        # Create labels
        df = labeler.create_labels(df)

        # Generate features
        df = feature_gen.generate_all_features(df)

        # Validate
        is_valid = feature_gen.validate_features(df)

        # Get feature list
        feature_cols = feature_gen.get_feature_columns(df)
        logger.info(f"Feature columns ({len(feature_cols)}): {feature_cols[:10]}...")

        # Save processed data
        output_dir = Path(config["data"]["data_dir"]) / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)

        if storage_format == "parquet":
            output_path = output_dir / f"{symbol}_features.parquet"
            df.to_parquet(output_path, index=False)
        else:
            output_path = output_dir / f"{symbol}_features.csv"
            df.to_csv(output_path, index=False)

        logger.info(f"Saved processed data to {output_path}")


if __name__ == "__main__":
    main()
