.PHONY: help install test data features train backtest tune report clean all

# Default target
help:
	@echo "Kronos Crypto Price Trend Prediction - Available targets:"
	@echo ""
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run test suite"
	@echo "  make data       - Download and prepare Binance data"
	@echo "  make features   - Generate features from raw data"
	@echo "  make train      - Train base model (simple split)"
	@echo "  make backtest   - Run walk-forward backtest"
	@echo "  make tune       - Hyperparameter optimization"
	@echo "  make report     - Generate accuracy reports"
	@echo "  make all        - Run complete pipeline (data → features → tune → backtest → report)"
	@echo "  make clean      - Clean generated files"
	@echo ""
	@echo "Quick start: make all"

# Install dependencies
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Dependencies installed successfully"

# Run test suite
test:
	@echo "Running test suite..."
	python tests/test_all.py
	@echo "All tests completed"

# Download and prepare data
data:
	@echo "Downloading Binance data..."
	python src/data_ingest.py
	@echo "Data download completed"

# Generate features
features:
	@echo "Generating features..."
	python src/features.py
	@echo "Feature generation completed"

# Train base model (simple split)
train:
	@echo "Training base model..."
	python src/model_kronos.py
	@echo "Model training completed"

# Run walk-forward backtest
backtest:
	@echo "Running walk-forward backtest..."
	python src/backtest.py
	@echo "Backtest completed"

# Hyperparameter tuning
tune:
	@echo "Running hyperparameter optimization..."
	python src/tune.py
	@echo "Hyperparameter tuning completed"

# Generate reports
report:
	@echo "Generating reports..."
	python src/report.py
	@echo "Reports generated in reports/"

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -rf data/processed
	rm -rf artifacts/*
	rm -rf reports/*
	rm -rf logs/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Clean completed"

# Run complete pipeline
all: data features tune backtest report
	@echo ""
	@echo "=========================================="
	@echo "Complete pipeline finished successfully!"
	@echo "=========================================="
	@echo ""
	@echo "Results:"
	@echo "  - Backtest metrics: artifacts/metrics_*.csv"
	@echo "  - Best parameters: artifacts/best_params_*.json"
	@echo "  - Reports: reports/"
	@echo "  - Summary: reports/summary.md"
	@echo ""
	@echo "View HTML reports: open reports/report_*.html"
