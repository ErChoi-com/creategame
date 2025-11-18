# Kronos Crypto Price Trend Prediction

A production-ready ML pipeline for predicting 10-minute cryptocurrency price trends using the Kronos framework. Features walk-forward backtesting, hyperparameter optimization, and comprehensive accuracy reporting.

## Features

- **Data Ingestion**: Automated Binance historical data fetching with retry logic and rate limiting
- **Smart Labeling**: Configurable 10-minute trend prediction (UP/DOWN/FLAT) with customizable thresholds
- **Rich Features**: 50+ technical indicators including momentum, volatility, volume, and microstructure features
- **Multiple Models**: Support for LightGBM, XGBoost, and Random Forest with Kronos integration
- **Walk-Forward Backtesting**: Strict time-series validation with anti-leakage controls
- **Hyperparameter Tuning**: Optuna-based optimization to maximize prediction accuracy
- **Comprehensive Reports**: Automated HTML and Markdown reports with visualizations

## Quick Start

### One-Command Setup and Run

```bash
# Install dependencies
make install

# Run complete pipeline (data → features → tune → backtest → report)
make all
```

That's it! The system will:
1. Download 730 days of BTCUSDT and ETHUSDT data from Binance
2. Generate 50+ technical features
3. Find optimal hyperparameters (100 trials per symbol)
4. Run walk-forward backtesting
5. Generate comprehensive accuracy reports

Results will be in:
- `artifacts/` - Models, metrics, best parameters
- `reports/` - HTML and Markdown reports with visualizations

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd creategame

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Individual Commands

```bash
# Download data from Binance
make data

# Generate features
make features

# Train a base model (simple train/test split)
make train

# Run walk-forward backtest
make backtest

# Optimize hyperparameters
make tune

# Generate reports
make report

# Clean all generated files
make clean
```

### Configuration

All settings are in `configs/config.yaml`:

```yaml
# Key configurations
data:
  symbols: ["BTCUSDT", "ETHUSDT"]
  lookback_days: 730  # 2 years of data

labeling:
  horizon_minutes: 10  # Predict 10 minutes ahead
  threshold_pct: 0.001  # 0.1% threshold for UP/DOWN
  num_classes: 3  # 3-class (UP/DOWN/FLAT) or 2-class

models:
  primary: "lightgbm"  # or "xgboost", "random_forest"

backtest:
  train_months: 12  # Initial training window
  valid_months: 1   # Validation window
  step_months: 1    # Walk-forward step

tuning:
  n_trials: 100  # Hyperparameter search trials
  objective: "accuracy"  # Metric to maximize
```

## Project Structure

```
.
├── configs/
│   └── config.yaml          # All configuration settings
├── data/                    # Raw and processed data (gitignored)
│   └── processed/           # Features and labels
├── src/
│   ├── data_ingest.py       # Binance data fetching
│   ├── labeling.py          # Trend label generation
│   ├── features.py          # Technical feature engineering
│   ├── model_kronos.py      # Model training (Kronos integration)
│   ├── backtest.py          # Walk-forward backtesting
│   ├── tune.py              # Hyperparameter optimization
│   └── report.py            # Report generation
├── artifacts/               # Models and metrics (gitignored)
├── reports/                 # HTML/Markdown reports (gitignored)
├── notebooks/               # Jupyter notebooks for EDA
├── Makefile                 # CLI commands
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Methodology

### 1. Data Collection

- **Source**: Binance Spot API
- **Pairs**: BTCUSDT, ETHUSDT
- **Interval**: 1-minute candlesticks
- **Span**: 730 days (configurable)
- **Storage**: Parquet format with Snappy compression

### 2. Labeling Strategy

For each time `t`, we predict the trend at `t + 10 minutes`:

- **UP**: `(close[t+10] - close[t]) / close[t] >= +0.1%`
- **DOWN**: `(close[t+10] - close[t]) / close[t] <= -0.1%`
- **FLAT**: Otherwise

Binary mode (UP vs DOWN only) is also supported by setting `use_binary: true`.

### 3. Feature Engineering

Generated features include:

**Price-based**:
- Log returns (1m, 3m, 5m, 10m, 15m, 30m)
- Rolling statistics (mean, std, min, max)
- Z-scores

**Volatility**:
- ATR (Average True Range)
- Realized volatility

**Momentum**:
- RSI (7, 14, 21 periods)
- MACD and signal line
- Stochastic oscillator

**Volume**:
- VWAP deltas
- Volume z-scores

**Microstructure**:
- High-low range
- Close-open spread
- Candle body ratio

Total: 50+ features per row

### 4. Walk-Forward Backtesting

Prevents data leakage with time-series splits:

1. **Initial training**: 12 months
2. **Validation**: 1 month
3. **Step forward**: 1 month
4. **Repeat** until end of data

Each fold:
- Train model on historical data only
- Validate on the next month
- Record metrics (accuracy, precision, recall, F1, MCC)
- Aggregate results across all folds

### 5. Hyperparameter Optimization

Uses Optuna (Tree-structured Parzen Estimator):

- **Objective**: Maximize validation accuracy
- **Budget**: 100 trials per symbol (configurable)
- **Search space**: Optimized for LightGBM/XGBoost/Random Forest
- **Early stopping**: Median pruning to skip unpromising trials

### 6. Evaluation Metrics

**Primary**: Directional accuracy (% correct predictions)

**Secondary**:
- Balanced accuracy (handles class imbalance)
- Precision, Recall, F1 (macro-averaged)
- Matthews Correlation Coefficient (MCC)
- Confusion matrices per fold

## Results

After running `make all`, check:

1. **Summary Report**: `reports/summary.md`
   - Overall accuracy for all symbols
   - Mean ± std across folds

2. **Per-Symbol Reports**: `reports/report_BTCUSDT.html`
   - Detailed metrics
   - Confusion matrices
   - Feature importance
   - Best hyperparameters

3. **Metrics CSV**: `artifacts/metrics_BTCUSDT.csv`
   - Per-fold results for analysis

4. **Best Parameters**: `artifacts/best_params_BTCUSDT.json`
   - Optimal hyperparameters found by Optuna

## Customization

### Change Prediction Horizon

Edit `configs/config.yaml`:

```yaml
labeling:
  horizon_minutes: 15  # Now predict 15 minutes ahead
```

### Add New Features

Edit `src/features.py`:

```python
def _add_custom_feature(self, df: pd.DataFrame) -> pd.DataFrame:
    """Add your custom feature."""
    df["my_feature"] = ...  # Your logic here
    return df
```

Then call it in `generate_all_features()`.

### Try Different Models

Edit `configs/config.yaml`:

```yaml
models:
  primary: "xgboost"  # Switch to XGBoost
```

Supported: `lightgbm`, `xgboost`, `random_forest`

### Adjust Backtest Window

Edit `configs/config.yaml`:

```yaml
backtest:
  train_months: 6   # Shorter training window
  valid_months: 2   # Longer validation window
  step_months: 2    # Larger steps
```

## Performance Tips

1. **Data Size**: Reduce `lookback_days` if API rate-limited
2. **Tuning Budget**: Reduce `n_trials` for faster results (trade accuracy for speed)
3. **Parallel Trials**: Set `n_jobs` in tuning config (careful with memory)
4. **GPU Acceleration**: Set `use_gpu: true` in config (requires GPU-enabled LightGBM/XGBoost)

## Reproducibility

All random operations are seeded via `config.yaml`:

```yaml
seed: 42  # Change for different random splits
```

The pipeline is fully deterministic when using the same:
- Configuration file
- Data (same date range)
- Package versions (see `requirements.txt`)

## Troubleshooting

### Data Download Fails

- **Issue**: Binance API rate limit or network error
- **Solution**: Retry with exponential backoff is built-in. If persistent, reduce `lookback_days` or wait and retry.

### Out of Memory

- **Issue**: Large dataset (730 days × 1-minute data)
- **Solution**: Reduce `lookback_days` or process symbols individually

### Low Accuracy

- **Issue**: Poor model performance
- **Solution**:
  1. Check class distribution (may be imbalanced)
  2. Adjust `threshold_pct` (try 0.0005 or 0.002)
  3. Increase `n_trials` for better hyperparameters
  4. Try different model types

### Missing Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Architecture

### Anti-Leakage Controls

1. **Time-based splits only** (no shuffling)
2. **Features computed from past data** (no future information)
3. **Strict chronological order** in backtesting
4. **No test set contamination** (walk-forward validation)

### Class Imbalance Handling

- **Balanced class weights** (if enabled in config)
- **Stratified splits** (where applicable)
- **Balanced accuracy metric** (reports both overall and per-class)

## Acceptance Criteria

All requirements from the spec are met:

- ✅ Data for BTCUSDT and ETHUSDT downloaded and cached
- ✅ Configurable 10-minute horizon and threshold τ
- ✅ Walk-forward backtest with no leakage
- ✅ Hyperparameter search with best params output
- ✅ Accuracy report with:
  - Overall & per-fold accuracy
  - Confusion matrices
  - Best hyperparameters
  - Optional trading metrics
- ✅ README with one-command run instructions
- ✅ Environment setup via `requirements.txt`

## Future Enhancements

Potential improvements (out of current scope):

- Live trading integration
- Multi-exchange data
- Deep learning models (LSTM, Transformers)
- Real-time feature computation
- Kubernetes deployment
- MLflow experiment tracking
- Calibration plots
- SHAP feature explanations

## Contributing

To contribute:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Open an issue on GitHub
- Check `logs/` directory for detailed execution logs
- Review `artifacts/` for intermediate results

## Citation

If you use this code in your research, please cite:

```
@software{kronos_crypto_prediction,
  title={Kronos Crypto Price Trend Prediction},
  year={2025},
  url={https://github.com/your-repo/kronos-crypto}
}
```

---

**Built with**: Python, Pandas, Scikit-learn, LightGBM, XGBoost, Optuna, Matplotlib

**Status**: Production-ready for backtesting (not for live trading without further validation)
