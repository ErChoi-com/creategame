"""
Backtesting Module for Walk-Forward Analysis

Implements time-series walk-forward backtesting with strict anti-leakage controls.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import json

from model_kronos import KronosModel

logger = logging.getLogger(__name__)


class WalkForwardBacktester:
    """
    Walk-forward backtesting with expanding or rolling window.

    Ensures no data leakage by:
    1. Time-based splits only (no shuffling)
    2. Features computed only from past data
    3. Strict chronological order
    """

    def __init__(self, config: Dict):
        """
        Initialize the backtester.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.backtest_config = config["backtest"]
        self.artifacts_dir = Path(config["reporting"]["artifacts_dir"])
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def create_folds(
        self, df: pd.DataFrame
    ) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
        """
        Create walk-forward folds.

        Args:
            df: DataFrame with time-sorted data

        Returns:
            List of (train_df, valid_df, fold_number) tuples
        """
        method = self.backtest_config["method"]
        train_months = self.backtest_config["train_months"]
        valid_months = self.backtest_config["valid_months"]
        step_months = self.backtest_config["step_months"]

        # Ensure data is sorted by time
        df = df.sort_values("open_time").reset_index(drop=True)

        # Get date range
        start_date = df["open_time"].min()
        end_date = df["open_time"].max()

        logger.info(f"Data range: {start_date} to {end_date}")
        logger.info(f"Backtest method: {method}")

        folds = []
        fold_num = 0

        # Initial training end date
        current_train_end = start_date + relativedelta(months=train_months)

        while True:
            # Validation period
            valid_start = current_train_end
            valid_end = valid_start + relativedelta(months=valid_months)

            # Check if we have enough data
            if valid_end > end_date:
                logger.info(f"Reached end of data at fold {fold_num}")
                break

            # Training period
            if method == "expanding":
                # Expanding window: train from start
                train_start = start_date
                train_end = current_train_end
            else:  # rolling
                # Rolling window: train for fixed period
                train_start = current_train_end - relativedelta(months=train_months)
                train_end = current_train_end

            # Create fold
            train_df = df[
                (df["open_time"] >= train_start) & (df["open_time"] < train_end)
            ].copy()

            valid_df = df[
                (df["open_time"] >= valid_start) & (df["open_time"] < valid_end)
            ].copy()

            # Ensure we have data
            if len(train_df) == 0 or len(valid_df) == 0:
                logger.warning(
                    f"Fold {fold_num} has insufficient data, skipping"
                )
                break

            logger.info(
                f"Fold {fold_num}: "
                f"Train {train_start.date()} to {train_end.date()} ({len(train_df)} samples), "
                f"Valid {valid_start.date()} to {valid_end.date()} ({len(valid_df)} samples)"
            )

            folds.append((train_df, valid_df, fold_num))

            # Move to next fold
            current_train_end += relativedelta(months=step_months)
            fold_num += 1

        logger.info(f"Created {len(folds)} folds")

        return folds

    def backtest_symbol(
        self,
        symbol: str,
        df: pd.DataFrame,
        params: Optional[Dict] = None,
        save_results: bool = True,
    ) -> Dict:
        """
        Run walk-forward backtest for a symbol.

        Args:
            symbol: Trading pair symbol
            df: DataFrame with features and labels
            params: Optional model parameters
            save_results: Whether to save results

        Returns:
            Dictionary with backtest results
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Backtesting {symbol}")
        logger.info(f"{'=' * 60}")

        # Create folds
        folds = self.create_folds(df)

        if len(folds) == 0:
            logger.error("No folds created, cannot backtest")
            return {}

        # Get feature columns
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

        # Store results
        fold_results = []

        for train_df, valid_df, fold_num in folds:
            logger.info(f"\nFold {fold_num}:")

            # Prepare data
            X_train = train_df[feature_cols]
            y_train = train_df["label"].values

            X_valid = valid_df[feature_cols]
            y_valid = valid_df["label"].values

            # Train model
            model = KronosModel(self.config)
            metrics = model.train(X_train, y_train, X_valid, y_valid, params=params)

            # Store fold results
            fold_result = {
                "fold": fold_num,
                "train_start": train_df["open_time"].min().isoformat(),
                "train_end": train_df["open_time"].max().isoformat(),
                "valid_start": valid_df["open_time"].min().isoformat(),
                "valid_end": valid_df["open_time"].max().isoformat(),
                "train_samples": len(train_df),
                "valid_samples": len(valid_df),
                **metrics,
            }

            fold_results.append(fold_result)

            # Log key metrics
            logger.info(f"  Train accuracy: {metrics['train_accuracy']:.4f}")
            logger.info(f"  Valid accuracy: {metrics['valid_accuracy']:.4f}")
            logger.info(f"  Valid balanced accuracy: {metrics['valid_balanced_accuracy']:.4f}")

            # Save confusion matrix for this fold
            if save_results:
                cm = metrics["valid_confusion_matrix"]
                cm_path = self.artifacts_dir / f"confusion_matrix_fold{fold_num}_{symbol}.npy"
                np.save(cm_path, cm)

        # Aggregate results
        aggregated = self._aggregate_results(fold_results)

        # Save results
        if save_results:
            results_path = self.artifacts_dir / f"backtest_results_{symbol}.json"
            with open(results_path, "w") as f:
                # Convert numpy arrays to lists for JSON serialization
                fold_results_json = []
                for fr in fold_results:
                    fr_copy = fr.copy()
                    for key, value in fr_copy.items():
                        if isinstance(value, np.ndarray):
                            fr_copy[key] = value.tolist()
                    fold_results_json.append(fr_copy)

                json.dump(
                    {
                        "symbol": symbol,
                        "num_folds": len(folds),
                        "fold_results": fold_results_json,
                        "aggregated": aggregated,
                    },
                    f,
                    indent=2,
                )

            logger.info(f"Results saved to {results_path}")

            # Save aggregated metrics as CSV
            metrics_df = pd.DataFrame(fold_results)
            metrics_df = metrics_df.drop(
                columns=[col for col in metrics_df.columns if "confusion_matrix" in col],
                errors="ignore",
            )
            metrics_path = self.artifacts_dir / f"metrics_{symbol}.csv"
            metrics_df.to_csv(metrics_path, index=False)
            logger.info(f"Metrics saved to {metrics_path}")

        return {
            "symbol": symbol,
            "fold_results": fold_results,
            "aggregated": aggregated,
        }

    def _aggregate_results(self, fold_results: List[Dict]) -> Dict:
        """
        Aggregate results across folds.

        Args:
            fold_results: List of fold result dictionaries

        Returns:
            Aggregated metrics
        """
        # Metrics to aggregate
        metric_keys = [
            "train_accuracy",
            "train_balanced_accuracy",
            "train_precision_macro",
            "train_recall_macro",
            "train_f1_macro",
            "train_mcc",
            "valid_accuracy",
            "valid_balanced_accuracy",
            "valid_precision_macro",
            "valid_recall_macro",
            "valid_f1_macro",
            "valid_mcc",
        ]

        aggregated = {}

        for key in metric_keys:
            values = [fr[key] for fr in fold_results if key in fr]
            if values:
                aggregated[f"{key}_mean"] = float(np.mean(values))
                aggregated[f"{key}_std"] = float(np.std(values))
                aggregated[f"{key}_min"] = float(np.min(values))
                aggregated[f"{key}_max"] = float(np.max(values))

        logger.info("\nAggregated Results:")
        logger.info(f"  Valid Accuracy: {aggregated['valid_accuracy_mean']:.4f} ± {aggregated['valid_accuracy_std']:.4f}")
        logger.info(f"  Valid Balanced Accuracy: {aggregated['valid_balanced_accuracy_mean']:.4f} ± {aggregated['valid_balanced_accuracy_std']:.4f}")
        logger.info(f"  Valid F1 (Macro): {aggregated['valid_f1_macro_mean']:.4f} ± {aggregated['valid_f1_macro_std']:.4f}")
        logger.info(f"  Valid MCC: {aggregated['valid_mcc_mean']:.4f} ± {aggregated['valid_mcc_std']:.4f}")

        return aggregated

    def run_all_symbols(
        self, symbols: List[str], params_dict: Optional[Dict[str, Dict]] = None
    ) -> Dict:
        """
        Run backtest for all symbols.

        Args:
            symbols: List of symbols to backtest
            params_dict: Optional dictionary of {symbol: params}

        Returns:
            Dictionary with all results
        """
        all_results = {}

        for symbol in symbols:
            # Load processed data
            data_dir = Path(self.config["data"]["data_dir"]) / "processed"
            storage_format = self.config["data"]["storage_format"]

            if storage_format == "parquet":
                filepath = data_dir / f"{symbol}_features.parquet"
                df = pd.read_parquet(filepath)
            else:
                filepath = data_dir / f"{symbol}_features.csv"
                df = pd.read_csv(filepath, parse_dates=["open_time"])

            # Get params for this symbol
            params = params_dict.get(symbol) if params_dict else None

            # Run backtest
            results = self.backtest_symbol(symbol, df, params=params)
            all_results[symbol] = results

        return all_results


class TradingSimulator:
    """Optional trading simulation for backtest."""

    def __init__(self, config: Dict):
        """
        Initialize the trading simulator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trading_config = config["backtest"]["trading_sim"]
        self.fee_pct = self.trading_config["fee_pct"]
        self.position_size = self.trading_config["position_size"]

    def simulate_trades(
        self, predictions: np.ndarray, actual_returns: np.ndarray
    ) -> Dict:
        """
        Simulate trading based on predictions.

        Args:
            predictions: Predicted labels (0=DOWN, 1=FLAT, 2=UP)
            actual_returns: Actual returns

        Returns:
            Dictionary with trading metrics
        """
        # Initialize equity
        equity = [1.0]  # Start with 1.0 (100%)

        for pred, ret in zip(predictions, actual_returns):
            # Determine position based on prediction
            if pred == 2:  # UP
                position = self.position_size
            elif pred == 0:  # DOWN
                position = -self.position_size
            else:  # FLAT
                position = 0

            # Calculate P&L
            gross_pnl = position * ret

            # Subtract fees
            if position != 0:
                net_pnl = gross_pnl - abs(position) * self.fee_pct * 2
            else:
                net_pnl = 0

            # Update equity
            new_equity = equity[-1] * (1 + net_pnl)
            equity.append(new_equity)

        equity = np.array(equity)

        # Calculate metrics
        total_return = (equity[-1] - 1.0) * 100
        max_equity = np.maximum.accumulate(equity)
        drawdown = (equity - max_equity) / max_equity * 100
        max_drawdown = drawdown.min()

        # Sharpe ratio (annualized, assuming 1-minute data)
        returns = np.diff(equity) / equity[:-1]
        sharpe = np.mean(returns) / np.std(returns) * np.sqrt(365 * 24 * 60) if np.std(returns) > 0 else 0

        metrics = {
            "total_return_pct": total_return,
            "max_drawdown_pct": max_drawdown,
            "sharpe_ratio": sharpe,
            "final_equity": equity[-1],
            "equity_curve": equity.tolist(),
        }

        return metrics


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

    # Create backtester
    backtester = WalkForwardBacktester(config)

    # Run backtest
    symbols = config["data"]["symbols"]
    results = backtester.run_all_symbols(symbols)

    logger.info("\n" + "=" * 60)
    logger.info("Backtest completed for all symbols")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
