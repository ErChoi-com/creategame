"""
Hyperparameter Tuning Module using Optuna

Searches for optimal hyperparameters to maximize validation accuracy.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, List
import json
import pandas as pd
import numpy as np
import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler

from model_kronos import KronosModel
from backtest import WalkForwardBacktester

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """Hyperparameter optimization using Optuna."""

    def __init__(self, config: Dict):
        """
        Initialize the tuner.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.tuning_config = config["tuning"]
        self.model_type = config["models"]["primary"]
        self.artifacts_dir = Path(config["reporting"]["artifacts_dir"])
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Set Optuna logging to WARNING to reduce verbosity
        optuna.logging.set_verbosity(optuna.logging.WARNING)

    def _suggest_params(self, trial: optuna.Trial) -> Dict:
        """
        Suggest hyperparameters for a trial.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of suggested parameters
        """
        search_space = self.tuning_config["search_space"].get(self.model_type, {})

        params = {}

        for param_name, param_config in search_space.items():
            param_type = param_config["type"]

            if param_type == "int":
                params[param_name] = trial.suggest_int(
                    param_name, param_config["low"], param_config["high"]
                )
            elif param_type == "uniform":
                params[param_name] = trial.suggest_uniform(
                    param_name, param_config["low"], param_config["high"]
                )
            elif param_type == "loguniform":
                params[param_name] = trial.suggest_loguniform(
                    param_name, param_config["low"], param_config["high"]
                )
            elif param_type == "categorical":
                params[param_name] = trial.suggest_categorical(
                    param_name, param_config["choices"]
                )
            else:
                logger.warning(f"Unknown parameter type: {param_type}")

        # Add fixed base parameters from model config
        base_params = self.config["models"].get(self.model_type, {}).copy()

        # Merge with suggested params (suggested params override base)
        final_params = {**base_params, **params}

        return final_params

    def _objective_simple(
        self,
        trial: optuna.Trial,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_valid: pd.DataFrame,
        y_valid: np.ndarray,
    ) -> float:
        """
        Objective function for simple train/valid split.

        Args:
            trial: Optuna trial
            X_train: Training features
            y_train: Training labels
            X_valid: Validation features
            y_valid: Validation labels

        Returns:
            Validation accuracy
        """
        # Suggest parameters
        params = self._suggest_params(trial)

        # Train model
        model = KronosModel(self.config, model_type=self.model_type)
        metrics = model.train(X_train, y_train, X_valid, y_valid, params=params)

        # Return validation accuracy (to maximize)
        objective_metric = self.tuning_config["objective"]
        return metrics.get(f"valid_{objective_metric}", 0.0)

    def _objective_walk_forward(
        self, trial: optuna.Trial, symbol: str, df: pd.DataFrame
    ) -> float:
        """
        Objective function using walk-forward validation.

        Args:
            trial: Optuna trial
            symbol: Trading pair symbol
            df: DataFrame with features and labels

        Returns:
            Average validation accuracy across folds
        """
        # Suggest parameters
        params = self._suggest_params(trial)

        # Create backtester
        backtester = WalkForwardBacktester(self.config)

        # Run backtest with suggested params
        results = backtester.backtest_symbol(
            symbol, df, params=params, save_results=False
        )

        # Get average validation accuracy
        objective_metric = self.tuning_config["objective"]
        fold_results = results.get("fold_results", [])

        if not fold_results:
            return 0.0

        scores = [fr.get(f"valid_{objective_metric}", 0.0) for fr in fold_results]
        avg_score = np.mean(scores)

        return avg_score

    def tune_symbol_simple(
        self,
        symbol: str,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_valid: pd.DataFrame,
        y_valid: np.ndarray,
    ) -> Dict:
        """
        Tune hyperparameters using simple train/valid split.

        Args:
            symbol: Trading pair symbol
            X_train: Training features
            y_train: Training labels
            X_valid: Validation features
            y_valid: Validation labels

        Returns:
            Dictionary with best parameters and study results
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Tuning hyperparameters for {symbol}")
        logger.info(f"{'=' * 60}")

        # Create study
        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=self.config["seed"]),
            pruner=MedianPruner(n_warmup_steps=10),
        )

        # Optimize
        n_trials = self.tuning_config["n_trials"]
        timeout = (
            self.tuning_config["timeout_hours"] * 3600
            if self.tuning_config["timeout_hours"]
            else None
        )

        logger.info(f"Running {n_trials} trials...")

        study.optimize(
            lambda trial: self._objective_simple(
                trial, X_train, y_train, X_valid, y_valid
            ),
            n_trials=n_trials,
            timeout=timeout,
            n_jobs=1,  # Sequential for now
            show_progress_bar=True,
        )

        # Get best parameters
        best_params = study.best_params
        best_value = study.best_value

        logger.info(f"\nBest parameters for {symbol}:")
        logger.info(json.dumps(best_params, indent=2))
        logger.info(f"Best validation accuracy: {best_value:.4f}")

        # Save results
        results = {
            "symbol": symbol,
            "model_type": self.model_type,
            "best_params": best_params,
            "best_value": best_value,
            "n_trials": len(study.trials),
        }

        # Save to file
        output_path = self.artifacts_dir / f"best_params_{symbol}.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved best parameters to {output_path}")

        return results

    def tune_symbol_walk_forward(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Tune hyperparameters using walk-forward validation.

        Args:
            symbol: Trading pair symbol
            df: DataFrame with features and labels

        Returns:
            Dictionary with best parameters and study results
        """
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Tuning hyperparameters for {symbol} (walk-forward)")
        logger.info(f"{'=' * 60}")

        # Create study
        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=self.config["seed"]),
            pruner=MedianPruner(n_warmup_steps=5),
        )

        # Optimize
        n_trials = self.tuning_config["n_trials"]
        timeout = (
            self.tuning_config["timeout_hours"] * 3600
            if self.tuning_config["timeout_hours"]
            else None
        )

        logger.info(f"Running {n_trials} trials with walk-forward validation...")

        study.optimize(
            lambda trial: self._objective_walk_forward(trial, symbol, df),
            n_trials=n_trials,
            timeout=timeout,
            n_jobs=1,  # Sequential to avoid data race
            show_progress_bar=True,
        )

        # Get best parameters
        best_params = study.best_params
        best_value = study.best_value

        logger.info(f"\nBest parameters for {symbol}:")
        logger.info(json.dumps(best_params, indent=2))
        logger.info(f"Best average validation accuracy: {best_value:.4f}")

        # Save results
        results = {
            "symbol": symbol,
            "model_type": self.model_type,
            "best_params": best_params,
            "best_value": best_value,
            "n_trials": len(study.trials),
        }

        # Save to file
        output_path = self.artifacts_dir / f"best_params_{symbol}.json"
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Saved best parameters to {output_path}")

        return results

    def tune_all_symbols(
        self, symbols: List[str], use_walk_forward: bool = True
    ) -> Dict[str, Dict]:
        """
        Tune hyperparameters for all symbols.

        Args:
            symbols: List of symbols to tune
            use_walk_forward: Whether to use walk-forward validation

        Returns:
            Dictionary of {symbol: results}
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

            if use_walk_forward:
                results = self.tune_symbol_walk_forward(symbol, df)
            else:
                # Simple train/valid split
                from sklearn.model_selection import train_test_split

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

                X = df[feature_cols]
                y = df["label"].values

                X_train, X_valid, y_train, y_valid = train_test_split(
                    X, y, test_size=0.2, random_state=self.config["seed"], stratify=y
                )

                results = self.tune_symbol_simple(
                    symbol, X_train, y_train, X_valid, y_valid
                )

            all_results[symbol] = results

        # Save combined results
        combined_path = self.artifacts_dir / "best_params_all.json"
        with open(combined_path, "w") as f:
            json.dump(all_results, f, indent=2)

        logger.info(f"\nSaved combined results to {combined_path}")

        return all_results

    def load_best_params(self, symbol: str) -> Optional[Dict]:
        """
        Load best parameters for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Best parameters or None if not found
        """
        filepath = self.artifacts_dir / f"best_params_{symbol}.json"

        if not filepath.exists():
            logger.warning(f"Best params not found for {symbol}")
            return None

        with open(filepath, "r") as f:
            results = json.load(f)

        return results.get("best_params")


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

    # Create tuner
    tuner = HyperparameterTuner(config)

    # Tune all symbols
    symbols = config["data"]["symbols"]
    results = tuner.tune_all_symbols(symbols, use_walk_forward=False)

    logger.info("\n" + "=" * 60)
    logger.info("Tuning completed for all symbols")
    logger.info("=" * 60)

    for symbol, result in results.items():
        logger.info(f"\n{symbol}:")
        logger.info(f"  Best accuracy: {result['best_value']:.4f}")
        logger.info(f"  Trials: {result['n_trials']}")


if __name__ == "__main__":
    main()
