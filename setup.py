"""
XnoxsFetcher Package Setup

Advanced TradingView Data Fetcher - A powerful Python library
for downloading historical and streaming live market data.

Author: developerxnoxs
License: MIT
"""

from setuptools import setup, find_packages
from pathlib import Path

README_PATH = Path(__file__).parent / "README.md"
long_description = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

setup(
    name="xnoxs_fetcher",
    version="3.0.0",
    author="developerxnoxs",
    author_email="developerxnoxs@gmail.com",
    description="Advanced TradingView historical and live data fetcher",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/developerxnoxs/xnoxs_fetcher",
    project_urls={
        "Bug Tracker": "https://github.com/developerxnoxs/xnoxs_fetcher/issues",
        "Source": "https://github.com/developerxnoxs/xnoxs_fetcher",
        "Documentation": "https://github.com/developerxnoxs/xnoxs_fetcher#readme",
    },
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*", "tvDatafeed"]),
    python_requires=">=3.9",
    install_requires=[
        "pandas>=2.0.0",
        "websocket-client>=1.0.0",
        "requests>=2.25.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords=[
        "tradingview",
        "trading",
        "stocks",
        "crypto",
        "cryptocurrency",
        "forex",
        "market-data",
        "historical-data",
        "live-data",
        "ohlcv",
        "pandas",
    ],
)
