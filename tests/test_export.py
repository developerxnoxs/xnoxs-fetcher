"""
Unit tests for DataExporter functionality.
"""

import pytest
import pandas as pd
from pathlib import Path
from xnoxs_fetcher import DataExporter, quick_export


class TestDataExporter:
    """Tests for DataExporter class."""

    def test_initialization(self, temp_export_dir):
        """Test exporter initialization."""
        exporter = DataExporter(output_dir=str(temp_export_dir))
        assert exporter is not None

    def test_export_csv(self, sample_ohlcv_data, temp_export_dir):
        """Test CSV export."""
        exporter = DataExporter(output_dir=str(temp_export_dir))
        filepath = exporter.to_csv(sample_ohlcv_data, "test_data")
        
        path = Path(filepath) if isinstance(filepath, str) else filepath
        assert path.exists()
        assert path.suffix == ".csv"
        
        loaded = pd.read_csv(path, index_col=0, parse_dates=True)
        assert len(loaded) == len(sample_ohlcv_data)

    def test_export_json(self, sample_ohlcv_data, temp_export_dir):
        """Test JSON export."""
        exporter = DataExporter(output_dir=str(temp_export_dir))
        filepath = exporter.to_json(sample_ohlcv_data, "test_data")
        
        path = Path(filepath) if isinstance(filepath, str) else filepath
        assert path.exists()
        assert path.suffix == ".json"

    def test_export_empty_dataframe(self, temp_export_dir):
        """Test exporting empty DataFrame."""
        exporter = DataExporter(output_dir=str(temp_export_dir))
        empty_df = pd.DataFrame()
        
        filepath = exporter.to_csv(empty_df, "empty_data")
        path = Path(filepath) if isinstance(filepath, str) else filepath
        assert path.exists()

    def test_create_summary_report(self, sample_ohlcv_data, temp_export_dir):
        """Test report generation."""
        exporter = DataExporter(output_dir=str(temp_export_dir))
        filepath = exporter.create_summary_report(sample_ohlcv_data, "test_report")
        
        path = Path(filepath) if isinstance(filepath, str) else filepath
        assert path.exists()
        
        content = path.read_text()
        assert "REPORT" in content.upper() or "DATA" in content.upper()


class TestQuickExport:
    """Tests for quick_export function."""

    def test_quick_export_csv(self, sample_ohlcv_data, tmp_path):
        """Test quick CSV export."""
        filename = str(tmp_path / "quick_test")
        filepath = quick_export(sample_ohlcv_data, filename, format="csv")
        assert Path(filepath).exists()

    def test_quick_export_json(self, sample_ohlcv_data, tmp_path):
        """Test quick JSON export."""
        filename = str(tmp_path / "quick_test")
        filepath = quick_export(sample_ohlcv_data, filename, format="json")
        assert Path(filepath).exists()


class TestExcelExport:
    """Tests for Excel export (requires openpyxl)."""

    def test_export_excel(self, sample_ohlcv_data, temp_export_dir):
        """Test Excel export."""
        pytest.importorskip("openpyxl")
        exporter = DataExporter(output_dir=str(temp_export_dir))
        filepath = exporter.to_excel(sample_ohlcv_data, "test_data")
        
        path = Path(filepath) if isinstance(filepath, str) else filepath
        assert path.exists()
        assert path.suffix == ".xlsx"
