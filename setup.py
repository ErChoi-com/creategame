"""
Setup configuration for Kronos Crypto Price Trend Prediction package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
requirements = []
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="kronos-crypto-prediction",
    version="1.0.0",
    author="Kronos Team",
    author_email="your.email@example.com",
    description="ML pipeline for cryptocurrency price trend prediction using Kronos framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/kronos-crypto",
    project_urls={
        "Bug Tracker": "https://github.com/your-repo/kronos-crypto/issues",
        "Documentation": "https://github.com/your-repo/kronos-crypto#readme",
        "Source Code": "https://github.com/your-repo/kronos-crypto",
    },
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "isort>=5.12.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "ipywidgets>=8.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kronos-data=src.data_ingest:main",
            "kronos-features=src.features:main",
            "kronos-train=src.model_kronos:main",
            "kronos-backtest=src.backtest:main",
            "kronos-tune=src.tune:main",
            "kronos-report=src.report:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.md"],
    },
    zip_safe=False,
    keywords="cryptocurrency trading machine-learning prediction backtesting kronos",
)
