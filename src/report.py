"""
Reporting Module for Backtest Results

Generates HTML and Markdown reports with visualizations.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

# Set plot style
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["font.size"] = 10


class ReportGenerator:
    """Generate comprehensive reports from backtest results."""

    def __init__(self, config: Dict):
        """
        Initialize the report generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.report_config = config["reporting"]
        self.artifacts_dir = Path(self.report_config["artifacts_dir"])
        self.reports_dir = Path(self.report_config["output_dir"])
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self, symbols: List[str]):
        """
        Generate reports for all symbols.

        Args:
            symbols: List of symbols to generate reports for
        """
        logger.info("Generating reports...")

        # Generate per-symbol reports
        for symbol in symbols:
            self.generate_symbol_report(symbol)

        # Generate combined report
        self.generate_summary_report(symbols)

        logger.info(f"Reports saved to {self.reports_dir}")

    def generate_symbol_report(self, symbol: str):
        """
        Generate report for a single symbol.

        Args:
            symbol: Trading pair symbol
        """
        logger.info(f"Generating report for {symbol}")

        # Load backtest results
        results_path = self.artifacts_dir / f"backtest_results_{symbol}.json"
        if not results_path.exists():
            logger.warning(f"Results not found for {symbol}, skipping")
            return

        with open(results_path, "r") as f:
            results = json.load(f)

        # Load metrics
        metrics_path = self.artifacts_dir / f"metrics_{symbol}.csv"
        if metrics_path.exists():
            metrics_df = pd.read_csv(metrics_path)
        else:
            metrics_df = pd.DataFrame(results["fold_results"])

        # Load best params
        params_path = self.artifacts_dir / f"best_params_{symbol}.json"
        best_params = None
        if params_path.exists():
            with open(params_path, "r") as f:
                best_params = json.load(f)

        # Load feature importance
        fi_path = self.artifacts_dir / f"feature_importance_{symbol}.csv"
        feature_importance = None
        if fi_path.exists():
            feature_importance = pd.read_csv(fi_path)

        # Generate plots
        self._plot_accuracy_over_time(symbol, metrics_df)
        self._plot_confusion_matrices(symbol, results)
        if feature_importance is not None:
            self._plot_feature_importance(symbol, feature_importance)

        # Generate HTML report
        if "html" in self.report_config["formats"]:
            self._generate_html_report(
                symbol, results, metrics_df, best_params, feature_importance
            )

        # Generate Markdown report
        if "markdown" in self.report_config["formats"]:
            self._generate_markdown_report(
                symbol, results, metrics_df, best_params, feature_importance
            )

    def _plot_accuracy_over_time(self, symbol: str, metrics_df: pd.DataFrame):
        """Plot accuracy over folds."""
        if "valid_accuracy" not in metrics_df.columns:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        ax.plot(
            metrics_df["fold"],
            metrics_df["valid_accuracy"],
            marker="o",
            label="Validation Accuracy",
            linewidth=2,
        )

        if "train_accuracy" in metrics_df.columns:
            ax.plot(
                metrics_df["fold"],
                metrics_df["train_accuracy"],
                marker="s",
                label="Train Accuracy",
                alpha=0.7,
                linewidth=2,
            )

        ax.set_xlabel("Fold")
        ax.set_ylabel("Accuracy")
        ax.set_title(f"Accuracy Over Time - {symbol}")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        output_path = self.reports_dir / f"accuracy_over_time_{symbol}.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Saved accuracy plot to {output_path}")

    def _plot_confusion_matrices(self, symbol: str, results: Dict):
        """Plot confusion matrices for all folds."""
        fold_results = results["fold_results"]
        num_folds = len(fold_results)

        if num_folds == 0:
            return

        # Create subplot grid
        ncols = min(3, num_folds)
        nrows = (num_folds + ncols - 1) // ncols

        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
        if num_folds == 1:
            axes = np.array([axes])
        axes = axes.flatten()

        for i, fold_result in enumerate(fold_results):
            cm = np.array(fold_result.get("valid_confusion_matrix", []))

            if cm.size == 0:
                # Try loading from file
                cm_path = self.artifacts_dir / f"confusion_matrix_fold{i}_{symbol}.npy"
                if cm_path.exists():
                    cm = np.load(cm_path)
                else:
                    continue

            ax = axes[i]

            # Plot confusion matrix
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                ax=ax,
                cbar=True,
                square=True,
            )

            ax.set_xlabel("Predicted")
            ax.set_ylabel("Actual")
            ax.set_title(f"Fold {i}")

            # Set labels based on number of classes
            if cm.shape[0] == 2:
                labels = ["DOWN", "UP"]
            else:
                labels = ["DOWN", "FLAT", "UP"]

            ax.set_xticklabels(labels)
            ax.set_yticklabels(labels)

        # Hide unused subplots
        for i in range(num_folds, len(axes)):
            axes[i].axis("off")

        plt.suptitle(f"Confusion Matrices - {symbol}", fontsize=14, y=1.0)
        plt.tight_layout()

        output_path = self.reports_dir / f"confusion_matrices_{symbol}.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Saved confusion matrices to {output_path}")

    def _plot_feature_importance(self, symbol: str, feature_importance: pd.DataFrame):
        """Plot feature importance."""
        # Plot top 20 features
        top_n = min(20, len(feature_importance))
        top_features = feature_importance.head(top_n)

        fig, ax = plt.subplots(figsize=(10, 8))

        ax.barh(range(top_n), top_features["importance"])
        ax.set_yticks(range(top_n))
        ax.set_yticklabels(top_features["feature"])
        ax.invert_yaxis()
        ax.set_xlabel("Importance")
        ax.set_title(f"Top {top_n} Feature Importance - {symbol}")
        ax.grid(True, alpha=0.3, axis="x")

        plt.tight_layout()
        output_path = self.reports_dir / f"feature_importance_{symbol}.png"
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info(f"Saved feature importance plot to {output_path}")

    def _generate_html_report(
        self,
        symbol: str,
        results: Dict,
        metrics_df: pd.DataFrame,
        best_params: Optional[Dict],
        feature_importance: Optional[pd.DataFrame],
    ):
        """Generate HTML report."""
        aggregated = results.get("aggregated", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report - {symbol}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metric {{ font-weight: bold; color: #4CAF50; }}
        .plot {{ margin: 20px 0; text-align: center; }}
        .plot img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Crypto Price Trend Prediction - Backtest Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Symbol:</strong> {symbol}</p>

        <h2>Summary Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Mean</th>
                <th>Std</th>
                <th>Min</th>
                <th>Max</th>
            </tr>
            <tr>
                <td>Validation Accuracy</td>
                <td class="metric">{aggregated.get('valid_accuracy_mean', 0):.4f}</td>
                <td>{aggregated.get('valid_accuracy_std', 0):.4f}</td>
                <td>{aggregated.get('valid_accuracy_min', 0):.4f}</td>
                <td>{aggregated.get('valid_accuracy_max', 0):.4f}</td>
            </tr>
            <tr>
                <td>Balanced Accuracy</td>
                <td class="metric">{aggregated.get('valid_balanced_accuracy_mean', 0):.4f}</td>
                <td>{aggregated.get('valid_balanced_accuracy_std', 0):.4f}</td>
                <td>{aggregated.get('valid_balanced_accuracy_min', 0):.4f}</td>
                <td>{aggregated.get('valid_balanced_accuracy_max', 0):.4f}</td>
            </tr>
            <tr>
                <td>F1 Score (Macro)</td>
                <td class="metric">{aggregated.get('valid_f1_macro_mean', 0):.4f}</td>
                <td>{aggregated.get('valid_f1_macro_std', 0):.4f}</td>
                <td>{aggregated.get('valid_f1_macro_min', 0):.4f}</td>
                <td>{aggregated.get('valid_f1_macro_max', 0):.4f}</td>
            </tr>
            <tr>
                <td>MCC</td>
                <td class="metric">{aggregated.get('valid_mcc_mean', 0):.4f}</td>
                <td>{aggregated.get('valid_mcc_std', 0):.4f}</td>
                <td>{aggregated.get('valid_mcc_min', 0):.4f}</td>
                <td>{aggregated.get('valid_mcc_max', 0):.4f}</td>
            </tr>
        </table>
"""

        if best_params:
            html += f"""
        <h2>Best Hyperparameters</h2>
        <pre>{json.dumps(best_params.get('best_params', {}), indent=2)}</pre>
        <p><strong>Best Validation Score:</strong> {best_params.get('best_value', 0):.4f}</p>
        <p><strong>Number of Trials:</strong> {best_params.get('n_trials', 0)}</p>
"""

        html += """
        <h2>Accuracy Over Time</h2>
        <div class="plot">
            <img src="accuracy_over_time_{}.png" alt="Accuracy Over Time">
        </div>

        <h2>Confusion Matrices</h2>
        <div class="plot">
            <img src="confusion_matrices_{}.png" alt="Confusion Matrices">
        </div>
""".format(
            symbol, symbol
        )

        if feature_importance is not None:
            html += """
        <h2>Feature Importance</h2>
        <div class="plot">
            <img src="feature_importance_{}.png" alt="Feature Importance">
        </div>
""".format(
                symbol
            )

        html += """
        <h2>Per-Fold Results</h2>
        {}
    </div>
</body>
</html>
""".format(
            metrics_df.to_html(index=False, classes="table")
        )

        # Save HTML
        output_path = self.reports_dir / f"report_{symbol}.html"
        with open(output_path, "w") as f:
            f.write(html)

        logger.info(f"Saved HTML report to {output_path}")

    def _generate_markdown_report(
        self,
        symbol: str,
        results: Dict,
        metrics_df: pd.DataFrame,
        best_params: Optional[Dict],
        feature_importance: Optional[pd.DataFrame],
    ):
        """Generate Markdown report."""
        aggregated = results.get("aggregated", {})

        md = f"""# Backtest Report - {symbol}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Metrics

| Metric | Mean | Std | Min | Max |
|--------|------|-----|-----|-----|
| Validation Accuracy | {aggregated.get('valid_accuracy_mean', 0):.4f} | {aggregated.get('valid_accuracy_std', 0):.4f} | {aggregated.get('valid_accuracy_min', 0):.4f} | {aggregated.get('valid_accuracy_max', 0):.4f} |
| Balanced Accuracy | {aggregated.get('valid_balanced_accuracy_mean', 0):.4f} | {aggregated.get('valid_balanced_accuracy_std', 0):.4f} | {aggregated.get('valid_balanced_accuracy_min', 0):.4f} | {aggregated.get('valid_balanced_accuracy_max', 0):.4f} |
| F1 Score (Macro) | {aggregated.get('valid_f1_macro_mean', 0):.4f} | {aggregated.get('valid_f1_macro_std', 0):.4f} | {aggregated.get('valid_f1_macro_min', 0):.4f} | {aggregated.get('valid_f1_macro_max', 0):.4f} |
| MCC | {aggregated.get('valid_mcc_mean', 0):.4f} | {aggregated.get('valid_mcc_std', 0):.4f} | {aggregated.get('valid_mcc_min', 0):.4f} | {aggregated.get('valid_mcc_max', 0):.4f} |

"""

        if best_params:
            md += f"""## Best Hyperparameters

```json
{json.dumps(best_params.get('best_params', {}), indent=2)}
```

**Best Validation Score:** {best_params.get('best_value', 0):.4f}
**Number of Trials:** {best_params.get('n_trials', 0)}

"""

        md += f"""## Visualizations

### Accuracy Over Time
![Accuracy Over Time](accuracy_over_time_{symbol}.png)

### Confusion Matrices
![Confusion Matrices](confusion_matrices_{symbol}.png)

"""

        if feature_importance is not None:
            md += f"""### Feature Importance
![Feature Importance](feature_importance_{symbol}.png)

"""

        md += f"""## Per-Fold Results

{metrics_df.to_markdown(index=False)}
"""

        # Save Markdown
        output_path = self.reports_dir / f"report_{symbol}.md"
        with open(output_path, "w") as f:
            f.write(md)

        logger.info(f"Saved Markdown report to {output_path}")

    def generate_summary_report(self, symbols: List[str]):
        """Generate summary report for all symbols."""
        logger.info("Generating summary report")

        summary_data = []

        for symbol in symbols:
            results_path = self.artifacts_dir / f"backtest_results_{symbol}.json"
            if not results_path.exists():
                continue

            with open(results_path, "r") as f:
                results = json.load(f)

            aggregated = results.get("aggregated", {})

            summary_data.append(
                {
                    "Symbol": symbol,
                    "Accuracy": f"{aggregated.get('valid_accuracy_mean', 0):.4f} ± {aggregated.get('valid_accuracy_std', 0):.4f}",
                    "Balanced Accuracy": f"{aggregated.get('valid_balanced_accuracy_mean', 0):.4f} ± {aggregated.get('valid_balanced_accuracy_std', 0):.4f}",
                    "F1 (Macro)": f"{aggregated.get('valid_f1_macro_mean', 0):.4f} ± {aggregated.get('valid_f1_macro_std', 0):.4f}",
                    "MCC": f"{aggregated.get('valid_mcc_mean', 0):.4f} ± {aggregated.get('valid_mcc_std', 0):.4f}",
                }
            )

        summary_df = pd.DataFrame(summary_data)

        # Save as CSV
        csv_path = self.reports_dir / "summary.csv"
        summary_df.to_csv(csv_path, index=False)

        # Generate Markdown
        md = f"""# Crypto Price Trend Prediction - Summary Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Results

{summary_df.to_markdown(index=False)}

## Configuration

**Model:** {self.config['models']['primary']}
**Prediction Horizon:** {self.config['labeling']['horizon_minutes']} minutes
**Number of Classes:** {self.config['labeling']['num_classes']}
**Threshold:** {self.config['labeling']['threshold_pct']} ({self.config['labeling']['threshold_pct'] * 100:.2f}%)

## Individual Reports

"""

        for symbol in symbols:
            md += f"- [{symbol}](report_{symbol}.html)\n"

        # Save summary
        md_path = self.reports_dir / "summary.md"
        with open(md_path, "w") as f:
            f.write(md)

        logger.info(f"Saved summary report to {md_path}")


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

    # Generate reports
    generator = ReportGenerator(config)
    symbols = config["data"]["symbols"]
    generator.generate_all_reports(symbols)

    logger.info("Report generation completed")


if __name__ == "__main__":
    main()
