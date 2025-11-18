"""
Labeling Module for Crypto Price Trend Prediction

Generates labels for predicting 10-minute price trends (UP/DOWN/FLAT).
"""

import logging
from typing import Dict, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class TrendLabeler:
    """Generate trend labels for price prediction."""

    def __init__(self, config: Dict):
        """
        Initialize the labeler.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.label_config = config["labeling"]
        self.horizon_minutes = self.label_config["horizon_minutes"]
        self.threshold_pct = self.label_config["threshold_pct"]
        self.num_classes = self.label_config["num_classes"]
        self.use_binary = self.label_config["use_binary"]

    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create trend labels based on future price movements.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added label column
        """
        df = df.copy()

        # Calculate future return
        # For 1-minute data, shift by horizon_minutes
        df["future_close"] = df["close"].shift(-self.horizon_minutes)

        # Calculate percentage return
        df["return_10m"] = (df["future_close"] - df["close"]) / df["close"]

        # Create labels based on threshold
        if self.use_binary:
            # Binary classification: UP (1) vs DOWN (0)
            df["label"] = (df["return_10m"] >= 0).astype(int)
            df.loc[df["return_10m"].isna(), "label"] = np.nan
        else:
            # 3-class classification: UP (2), DOWN (0), FLAT (1)
            df["label"] = 1  # Default to FLAT

            # UP: return >= threshold
            df.loc[df["return_10m"] >= self.threshold_pct, "label"] = 2

            # DOWN: return <= -threshold
            df.loc[df["return_10m"] <= -self.threshold_pct, "label"] = 0

            # Set NaN for rows without future data
            df.loc[df["return_10m"].isna(), "label"] = np.nan

        # Drop rows with NaN labels (last horizon_minutes rows)
        initial_len = len(df)
        df = df.dropna(subset=["label"])
        logger.info(
            f"Dropped {initial_len - len(df)} rows without labels (last {self.horizon_minutes} minutes)"
        )

        # Convert label to int
        df["label"] = df["label"].astype(int)

        return df

    def get_label_distribution(self, df: pd.DataFrame) -> Dict:
        """
        Get the distribution of labels.

        Args:
            df: DataFrame with labels

        Returns:
            Dictionary with label counts and percentages
        """
        if "label" not in df.columns:
            raise ValueError("DataFrame must have a 'label' column")

        label_counts = df["label"].value_counts().sort_index()
        label_pcts = df["label"].value_counts(normalize=True).sort_index() * 100

        distribution = {}
        label_names = (
            {0: "DOWN", 1: "UP"}
            if self.use_binary
            else {0: "DOWN", 1: "FLAT", 2: "UP"}
        )

        for label_id, label_name in label_names.items():
            count = label_counts.get(label_id, 0)
            pct = label_pcts.get(label_id, 0.0)
            distribution[label_name] = {"count": int(count), "percentage": float(pct)}

        return distribution

    def validate_labels(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate that labels are correctly generated.

        Args:
            df: DataFrame with labels

        Returns:
            Tuple of (is_valid, message)
        """
        if "label" not in df.columns:
            return False, "Label column not found"

        # Check for NaN labels
        if df["label"].isna().any():
            return False, "Found NaN values in labels"

        # Check label values
        unique_labels = df["label"].unique()

        if self.use_binary:
            expected_labels = {0, 1}
            if not set(unique_labels).issubset(expected_labels):
                return (
                    False,
                    f"Invalid labels for binary classification. Expected {expected_labels}, got {unique_labels}",
                )
        else:
            expected_labels = {0, 1, 2}
            if not set(unique_labels).issubset(expected_labels):
                return (
                    False,
                    f"Invalid labels for 3-class classification. Expected {expected_labels}, got {unique_labels}",
                )

        # Check for class imbalance (warn if one class < 5%)
        distribution = self.get_label_distribution(df)
        for label_name, stats in distribution.items():
            if stats["percentage"] < 5.0:
                logger.warning(
                    f"Class {label_name} has only {stats['percentage']:.2f}% of data"
                )

        return True, "Labels are valid"

    def analyze_returns(self, df: pd.DataFrame) -> Dict:
        """
        Analyze the distribution of returns.

        Args:
            df: DataFrame with return_10m column

        Returns:
            Dictionary with statistics
        """
        if "return_10m" not in df.columns:
            raise ValueError("DataFrame must have a 'return_10m' column")

        returns = df["return_10m"].dropna()

        stats = {
            "count": len(returns),
            "mean": float(returns.mean()),
            "std": float(returns.std()),
            "min": float(returns.min()),
            "max": float(returns.max()),
            "median": float(returns.median()),
            "q25": float(returns.quantile(0.25)),
            "q75": float(returns.quantile(0.75)),
            "positive_pct": float((returns > 0).mean() * 100),
            "negative_pct": float((returns < 0).mean() * 100),
            "zero_pct": float((returns == 0).mean() * 100),
        }

        # Add threshold-based stats
        stats[f"above_threshold_pct"] = float(
            (returns >= self.threshold_pct).mean() * 100
        )
        stats[f"below_threshold_pct"] = float(
            (returns <= -self.threshold_pct).mean() * 100
        )
        stats[f"within_threshold_pct"] = float(
            ((returns > -self.threshold_pct) & (returns < self.threshold_pct)).mean()
            * 100
        )

        return stats


def main():
    """Main function for standalone testing."""
    import yaml
    from pathlib import Path
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

    # Load data
    data_dir = Path(config["data"]["data_dir"])
    symbols = config["data"]["symbols"]

    labeler = TrendLabeler(config)

    for symbol in symbols:
        logger.info(f"\nProcessing {symbol}")

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
        df_labeled = labeler.create_labels(df)
        logger.info(f"Created labels for {len(df_labeled)} records")

        # Get distribution
        distribution = labeler.get_label_distribution(df_labeled)
        logger.info(f"Label distribution: {distribution}")

        # Validate
        is_valid, message = labeler.validate_labels(df_labeled)
        logger.info(f"Validation: {message}")

        # Analyze returns
        stats = labeler.analyze_returns(df_labeled)
        logger.info(f"Return statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value:.6f}")


if __name__ == "__main__":
    main()
