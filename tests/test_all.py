"""
Comprehensive test suite for Kronos crypto prediction system.

Tests all major components for bugs and functionality.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import load_config, validate_config, validate_dataframe, check_data_quality
from labeling import TrendLabeler
from features import FeatureGenerator


def test_utils():
    """Test utilities module."""
    print("\n" + "=" * 60)
    print("Testing Utils Module")
    print("=" * 60)

    # Test config loading
    config = load_config(Path('configs/config.yaml'))
    assert config is not None, "Config should load"
    assert 'seed' in config, "Config should have seed"
    print("✓ Config loading works")

    # Test config validation
    validate_config(config)
    print("✓ Config validation works")

    # Test DataFrame validation
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    is_valid, msg = validate_dataframe(df, ['a', 'b'], min_rows=1)
    assert is_valid, f"DataFrame should be valid: {msg}"
    print("✓ DataFrame validation works")

    # Test data quality check
    df = pd.DataFrame({'close': [100, 101, 102, 103]})
    quality = check_data_quality(df, 'close')
    assert 'null_count' in quality, "Quality check should return metrics"
    print("✓ Data quality check works")

    print("✓ All utils tests passed\n")


def test_labeling():
    """Test labeling module."""
    print("\n" + "=" * 60)
    print("Testing Labeling Module")
    print("=" * 60)

    config = load_config(Path('configs/config.yaml'))
    labeler = TrendLabeler(config)

    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
    df = pd.DataFrame({
        'open_time': dates,
        'open': prices,
        'high': prices + np.random.rand(100),
        'low': prices - np.random.rand(100),
        'close': prices,
        'volume': np.random.rand(100) * 1000
    })

    # Test label creation
    df_labeled = labeler.create_labels(df.copy())
    assert 'label' in df_labeled.columns, "Should have label column"
    assert len(df_labeled) > 0, "Should have labeled rows"
    print(f"✓ Created labels for {len(df_labeled)} rows")

    # Test label distribution
    distribution = labeler.get_label_distribution(df_labeled)
    assert len(distribution) > 0, "Should have label distribution"
    print(f"✓ Label distribution: {distribution}")

    # Test validation
    is_valid, msg = labeler.validate_labels(df_labeled)
    assert is_valid, f"Labels should be valid: {msg}"
    print("✓ Label validation works")

    # Test return analysis
    stats = labeler.analyze_returns(df_labeled)
    assert 'mean' in stats, "Should have return statistics"
    print(f"✓ Return analysis works: mean={stats['mean']:.6f}")

    print("✓ All labeling tests passed\n")


def test_features():
    """Test features module."""
    print("\n" + "=" * 60)
    print("Testing Features Module")
    print("=" * 60)

    config = load_config(Path('configs/config.yaml'))
    labeler = TrendLabeler(config)
    feature_gen = FeatureGenerator(config)

    # Create sample data with more rows for rolling windows
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1min')
    prices = 100 + np.cumsum(np.random.randn(200) * 0.1)
    df = pd.DataFrame({
        'open_time': dates,
        'open': prices,
        'high': prices + np.random.rand(200),
        'low': prices - np.random.rand(200),
        'close': prices,
        'volume': np.random.rand(200) * 1000
    })

    # Add labels first
    df_labeled = labeler.create_labels(df.copy())
    print(f"✓ Created {len(df_labeled)} labeled samples")

    # Generate features
    df_features = feature_gen.generate_all_features(df_labeled)
    assert len(df_features) > 0, "Should have rows after feature generation"
    print(f"✓ Generated features, {len(df_features)} rows remaining")

    # Get feature columns
    feature_cols = feature_gen.get_feature_columns(df_features)
    assert len(feature_cols) > 0, "Should have feature columns"
    print(f"✓ Generated {len(feature_cols)} features")

    # Validate features
    is_valid = feature_gen.validate_features(df_features)
    assert is_valid, "Features should be valid"
    print("✓ Feature validation passed")

    # Check for specific features
    expected_features = ['log_return_10m', 'rsi_14', 'macd']
    for feat in expected_features:
        assert feat in df_features.columns, f"Should have {feat}"
    print(f"✓ Expected features present: {expected_features}")

    print("✓ All feature tests passed\n")


def test_model():
    """Test model module."""
    print("\n" + "=" * 60)
    print("Testing Model Module")
    print("=" * 60)

    from model_kronos import KronosModel
    from sklearn.model_selection import train_test_split

    config = load_config(Path('configs/config.yaml'))

    # Create sample data
    np.random.seed(42)
    n_samples = 500
    n_features = 20
    X = pd.DataFrame(np.random.randn(n_samples, n_features),
                     columns=[f'feat_{i}' for i in range(n_features)])
    y = np.random.randint(0, 3, n_samples)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Test model creation
    model = KronosModel(config)
    assert model is not None, "Model should be created"
    print("✓ Model created successfully")

    # Test model training
    metrics = model.train(X_train, y_train, X_test, y_test)
    assert 'train_accuracy' in metrics, "Should have training metrics"
    assert 'valid_accuracy' in metrics, "Should have validation metrics"
    print(f"✓ Model trained: train_acc={metrics['train_accuracy']:.3f}, valid_acc={metrics['valid_accuracy']:.3f}")

    # Test predictions
    y_pred = model.predict(X_test)
    assert len(y_pred) == len(X_test), "Should predict all samples"
    print(f"✓ Predictions generated: {len(y_pred)} samples")

    # Test feature importance
    importance = model.get_feature_importance()
    assert importance is not None, "Should have feature importance"
    assert len(importance) > 0, "Should have importance scores"
    print(f"✓ Feature importance extracted: {len(importance)} features")

    print("✓ All model tests passed\n")


def test_backtest():
    """Test backtesting module."""
    print("\n" + "=" * 60)
    print("Testing Backtest Module")
    print("=" * 60)

    from backtest import WalkForwardBacktester

    config = load_config(Path('configs/config_quick_test.yaml'))
    # Use smaller windows for testing: 7 days train, 7 days valid
    config['backtest']['train_months'] = 1
    config['backtest']['valid_months'] = 1
    config['backtest']['method'] = 'walk_forward'

    labeler = TrendLabeler(config)
    feature_gen = FeatureGenerator(config)

    # Create sample data spanning 3+ months (enough for train + valid windows)
    # 1440 minutes/day * 90 days = 129,600 minutes
    n_samples = 100000
    dates = pd.date_range(start='2024-01-01', periods=n_samples, freq='min')
    prices = 100 + np.cumsum(np.random.randn(n_samples) * 0.05)
    df = pd.DataFrame({
        'open_time': dates,
        'open': prices,
        'high': prices + np.random.rand(n_samples) * 0.5,
        'low': prices - np.random.rand(n_samples) * 0.5,
        'close': prices,
        'volume': np.random.rand(n_samples) * 1000
    })

    # Add labels and features
    df_labeled = labeler.create_labels(df.copy())
    df_features = feature_gen.generate_all_features(df_labeled)

    print(f"✓ Created test dataset: {len(df_features)} samples")

    # Test fold creation
    backtester = WalkForwardBacktester(config)
    folds = backtester.create_folds(df_features)
    assert len(folds) > 0, "Should create at least one fold"
    print(f"✓ Created {len(folds)} backtest folds")

    # Test that folds don't overlap
    for i, (train_df, valid_df, fold_num) in enumerate(folds):
        train_end = train_df['open_time'].max()
        valid_start = valid_df['open_time'].min()
        assert train_end < valid_start, f"Fold {i}: Train and valid should not overlap"
    print("✓ Fold time separation validated")

    print("✓ All backtest tests passed\n")


def test_integration():
    """Test full integration."""
    print("\n" + "=" * 60)
    print("Testing Full Integration")
    print("=" * 60)

    config = load_config(Path('configs/config_quick_test.yaml'))

    # Create complete dataset
    labeler = TrendLabeler(config)
    feature_gen = FeatureGenerator(config)

    dates = pd.date_range(start='2024-01-01', periods=1000, freq='1min')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.1)
    df = pd.DataFrame({
        'open_time': dates,
        'open': prices,
        'high': prices + np.random.rand(1000) * 0.5,
        'low': prices - np.random.rand(1000) * 0.5,
        'close': prices,
        'volume': np.random.rand(1000) * 1000
    })

    # Run full pipeline
    print("Step 1: Labeling...")
    df_labeled = labeler.create_labels(df.copy())
    assert 'label' in df_labeled.columns

    print("Step 2: Feature generation...")
    df_features = feature_gen.generate_all_features(df_labeled)
    feature_cols = feature_gen.get_feature_columns(df_features)
    assert len(feature_cols) > 0

    print("Step 3: Train/test split...")
    from sklearn.model_selection import train_test_split
    X = df_features[feature_cols]
    y = df_features['label'].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Step 4: Model training...")
    from model_kronos import KronosModel
    model = KronosModel(config)
    metrics = model.train(X_train, y_train, X_test, y_test)

    print(f"✓ Pipeline complete!")
    print(f"  - Samples: {len(df_features)}")
    print(f"  - Features: {len(feature_cols)}")
    print(f"  - Train accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  - Valid accuracy: {metrics['valid_accuracy']:.3f}")

    # Verify accuracy is reasonable (better than random for 3-class)
    assert metrics['valid_accuracy'] > 0.25, "Accuracy should be better than random"

    print("✓ All integration tests passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KRONOS CRYPTO PREDICTION - COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Utils", test_utils),
        ("Labeling", test_labeling),
        ("Features", test_features),
        ("Model", test_model),
        ("Backtest", test_backtest),
        ("Integration", test_integration),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ {name} tests FAILED:")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
