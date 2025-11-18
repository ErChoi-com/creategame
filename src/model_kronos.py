"""
Model Training Module with Kronos Integration

Provides model training functionality compatible with Kronos framework.
Supports LightGBM, XGBoost, Random Forest, and other classifiers.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    confusion_matrix,
)

# Import models
import lightgbm as lgb
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier

logger = logging.getLogger(__name__)


class KronosModel:
    """
    Wrapper for machine learning models with Kronos-compatible interface.

    Supports multiple model families: LightGBM, XGBoost, Random Forest.
    """

    def __init__(self, config: Dict, model_type: Optional[str] = None):
        """
        Initialize the model.

        Args:
            config: Configuration dictionary
            model_type: Model type override (default: from config)
        """
        self.config = config
        self.model_config = config["models"]
        self.model_type = model_type or self.model_config["primary"]
        self.seed = config["seed"]
        self.model = None
        self.feature_names = None
        self.num_classes = config["labeling"]["num_classes"]

    def _get_class_weights(self, y: np.ndarray) -> Optional[Dict]:
        """
        Compute class weights for imbalanced data.

        Args:
            y: Target labels

        Returns:
            Dictionary of class weights or None
        """
        if not self.model_config["handle_imbalance"]:
            return None

        classes = np.unique(y)
        weights = compute_class_weight(
            class_weight="balanced", classes=classes, y=y
        )

        class_weight_dict = {int(cls): float(weight) for cls, weight in zip(classes, weights)}
        logger.info(f"Class weights: {class_weight_dict}")

        return class_weight_dict

    def build_model(self, params: Optional[Dict] = None) -> Any:
        """
        Build the model based on configuration.

        Args:
            params: Optional parameter overrides

        Returns:
            Model instance
        """
        # Get base parameters
        if params is None:
            params = self.model_config.get(self.model_type, {}).copy()
        else:
            params = params.copy()

        # Add seed for reproducibility
        if self.model_type == "lightgbm":
            params["random_state"] = self.seed
            params["verbose"] = -1
            model = lgb.LGBMClassifier(**params)

        elif self.model_type == "xgboost":
            params["random_state"] = self.seed
            params["verbosity"] = 0
            model = xgb.XGBClassifier(**params)

        elif self.model_type == "random_forest":
            params["random_state"] = self.seed
            model = RandomForestClassifier(**params)

        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        logger.info(f"Built {self.model_type} model with params: {params}")

        return model

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_valid: Optional[pd.DataFrame] = None,
        y_valid: Optional[np.ndarray] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        """
        Train the model.

        Args:
            X_train: Training features
            y_train: Training labels
            X_valid: Validation features
            y_valid: Validation labels
            params: Optional parameter overrides

        Returns:
            Dictionary with training metrics
        """
        logger.info(
            f"Training {self.model_type} on {len(X_train)} samples, "
            f"{len(X_train.columns)} features"
        )

        # Store feature names
        self.feature_names = list(X_train.columns)

        # Build model
        self.model = self.build_model(params)

        # Compute class weights
        class_weights = self._get_class_weights(y_train)

        # Train model
        if self.model_type == "lightgbm":
            if class_weights and hasattr(self.model, "set_params"):
                self.model.set_params(class_weight=class_weights)

            if X_valid is not None and y_valid is not None:
                self.model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_valid, y_valid)],
                    callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
                )
            else:
                self.model.fit(X_train, y_train)

        elif self.model_type == "xgboost":
            # XGBoost uses sample_weight instead of class_weight
            sample_weights = None
            if class_weights:
                sample_weights = np.array([class_weights[int(label)] for label in y_train])

            if X_valid is not None and y_valid is not None:
                self.model.fit(
                    X_train,
                    y_train,
                    sample_weight=sample_weights,
                    eval_set=[(X_valid, y_valid)],
                    verbose=False,
                )
            else:
                self.model.fit(X_train, y_train, sample_weight=sample_weights)

        elif self.model_type == "random_forest":
            if class_weights and hasattr(self.model, "set_params"):
                self.model.set_params(class_weight=class_weights)

            self.model.fit(X_train, y_train)

        # Evaluate on training set
        train_metrics = self.evaluate(X_train, y_train, prefix="train")

        # Evaluate on validation set if provided
        valid_metrics = {}
        if X_valid is not None and y_valid is not None:
            valid_metrics = self.evaluate(X_valid, y_valid, prefix="valid")

        metrics = {**train_metrics, **valid_metrics}

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make predictions.

        Args:
            X: Features

        Returns:
            Predicted labels
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: Features

        Returns:
            Predicted probabilities
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict_proba(X)

    def evaluate(self, X: pd.DataFrame, y: np.ndarray, prefix: str = "") -> Dict:
        """
        Evaluate the model.

        Args:
            X: Features
            y: True labels
            prefix: Prefix for metric names

        Returns:
            Dictionary with evaluation metrics
        """
        y_pred = self.predict(X)

        metrics = {
            f"{prefix}_accuracy": accuracy_score(y, y_pred),
            f"{prefix}_balanced_accuracy": balanced_accuracy_score(y, y_pred),
            f"{prefix}_precision_macro": precision_score(
                y, y_pred, average="macro", zero_division=0
            ),
            f"{prefix}_recall_macro": recall_score(
                y, y_pred, average="macro", zero_division=0
            ),
            f"{prefix}_f1_macro": f1_score(y, y_pred, average="macro", zero_division=0),
            f"{prefix}_mcc": matthews_corrcoef(y, y_pred),
        }

        # Add per-class metrics
        precision_per_class = precision_score(y, y_pred, average=None, zero_division=0)
        recall_per_class = recall_score(y, y_pred, average=None, zero_division=0)
        f1_per_class = f1_score(y, y_pred, average=None, zero_division=0)

        for i in range(len(precision_per_class)):
            metrics[f"{prefix}_precision_class_{i}"] = precision_per_class[i]
            metrics[f"{prefix}_recall_class_{i}"] = recall_per_class[i]
            metrics[f"{prefix}_f1_class_{i}"] = f1_per_class[i]

        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        metrics[f"{prefix}_confusion_matrix"] = cm

        return metrics

    def get_feature_importance(self) -> Optional[pd.DataFrame]:
        """
        Get feature importance.

        Returns:
            DataFrame with feature importance or None
        """
        if self.model is None:
            return None

        if hasattr(self.model, "feature_importances_"):
            importance_df = pd.DataFrame(
                {
                    "feature": self.feature_names,
                    "importance": self.model.feature_importances_,
                }
            )
            importance_df = importance_df.sort_values("importance", ascending=False)
            return importance_df
        else:
            logger.warning(f"Model {self.model_type} does not have feature_importances_")
            return None

    def save(self, filepath: Path):
        """
        Save the model to disk.

        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save")

        filepath.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "model": self.model,
            "model_type": self.model_type,
            "feature_names": self.feature_names,
            "config": self.config,
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {filepath}")

    def load(self, filepath: Path):
        """
        Load a model from disk.

        Args:
            filepath: Path to the model file
        """
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.model = model_data["model"]
        self.model_type = model_data["model_type"]
        self.feature_names = model_data["feature_names"]

        logger.info(f"Model loaded from {filepath}")


class ModelTrainer:
    """High-level interface for training models."""

    def __init__(self, config: Dict):
        """
        Initialize the trainer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.artifacts_dir = Path(config["reporting"]["artifacts_dir"])
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def train_model(
        self,
        symbol: str,
        X_train: pd.DataFrame,
        y_train: np.ndarray,
        X_valid: pd.DataFrame,
        y_valid: np.ndarray,
        params: Optional[Dict] = None,
        save_model: bool = True,
    ) -> Tuple[KronosModel, Dict]:
        """
        Train a model for a specific symbol.

        Args:
            symbol: Trading pair symbol
            X_train: Training features
            y_train: Training labels
            X_valid: Validation features
            y_valid: Validation labels
            params: Optional parameter overrides
            save_model: Whether to save the trained model

        Returns:
            Tuple of (trained model, metrics)
        """
        logger.info(f"Training model for {symbol}")

        model = KronosModel(self.config)
        metrics = model.train(X_train, y_train, X_valid, y_valid, params=params)

        # Log metrics
        logger.info(f"Training metrics for {symbol}:")
        for key, value in metrics.items():
            if not isinstance(value, np.ndarray):
                logger.info(f"  {key}: {value:.4f}")

        # Save model
        if save_model:
            model_path = self.artifacts_dir / f"model_{symbol}.pkl"
            model.save(model_path)

        # Save feature importance
        feature_importance = model.get_feature_importance()
        if feature_importance is not None:
            fi_path = self.artifacts_dir / f"feature_importance_{symbol}.csv"
            feature_importance.to_csv(fi_path, index=False)
            logger.info(f"Feature importance saved to {fi_path}")

        return model, metrics


def main():
    """Main function for standalone testing."""
    import yaml
    import sys
    from sklearn.model_selection import train_test_split

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

    # Load processed data
    data_dir = Path(config["data"]["data_dir"]) / "processed"
    symbols = config["data"]["symbols"]

    trainer = ModelTrainer(config)

    for symbol in symbols:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Training {symbol}")
        logger.info(f"{'=' * 60}")

        # Load data
        storage_format = config["data"]["storage_format"]
        if storage_format == "parquet":
            filepath = data_dir / f"{symbol}_features.parquet"
            df = pd.read_parquet(filepath)
        else:
            filepath = data_dir / f"{symbol}_features.csv"
            df = pd.read_csv(filepath, parse_dates=["open_time"])

        # Prepare features and labels
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

        # Split data
        X_train, X_valid, y_train, y_valid = train_test_split(
            X, y, test_size=0.2, random_state=config["seed"], stratify=y
        )

        # Train model
        model, metrics = trainer.train_model(
            symbol, X_train, y_train, X_valid, y_valid
        )

        logger.info(f"Completed training for {symbol}")


if __name__ == "__main__":
    main()
