"""
Kronos Crypto Price Trend Prediction Package

A production-ready ML pipeline for cryptocurrency price trend prediction.
"""

__version__ = "1.0.0"
__author__ = "Kronos Team"

from . import data_ingest
from . import labeling
from . import features
from . import model_kronos
from . import backtest
from . import tune
from . import report

__all__ = [
    "data_ingest",
    "labeling",
    "features",
    "model_kronos",
    "backtest",
    "tune",
    "report",
]
