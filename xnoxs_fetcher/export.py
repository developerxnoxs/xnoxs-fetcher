"""
XnoxsFetcher Export Module

This module provides data export functionality to various formats
including CSV, Excel, and JSON.

Author: developerxnoxs
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Union

import pandas as pd

logger = logging.getLogger(__name__)


class DataExporter:
    """
    Export market data to various file formats.
    
    Supported formats:
        - CSV (Comma Separated Values)
        - Excel (.xlsx)
        - JSON
        - Parquet (for large datasets)
    
    Example:
        >>> exporter = DataExporter()
        >>> exporter.to_csv(df, "AAPL_daily.csv")
        >>> exporter.to_excel(df, "portfolio.xlsx", sheet_name="AAPL")
    
    Author: developerxnoxs
    """
    
    def __init__(self, output_dir: str = "exports"):
        """
        Initialize DataExporter.
        
        Args:
            output_dir: Default directory for exported files
        """
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    def _prepare_dataframe(
        self, 
        df: pd.DataFrame,
        include_symbol: bool = True
    ) -> pd.DataFrame:
        """Prepare DataFrame for export."""
        export_df = df.copy()
        
        if export_df.index.name == 'datetime' or isinstance(export_df.index, pd.DatetimeIndex):
            export_df = export_df.reset_index()
        
        if 'datetime' in export_df.columns:
            export_df['datetime'] = export_df['datetime'].astype(str)
        
        if not include_symbol and 'symbol' in export_df.columns:
            export_df = export_df.drop(columns=['symbol'])
        
        return export_df
    
    def _get_filepath(
        self, 
        filename: str, 
        extension: str
    ) -> Path:
        """Get full filepath with extension."""
        if not filename.endswith(extension):
            filename = f"{filename}{extension}"
        
        if "/" in filename or "\\" in filename:
            return Path(filename)
        
        return self._output_dir / filename
    
    def to_csv(
        self,
        data: Union[pd.DataFrame, List[pd.DataFrame]],
        filename: str,
        include_symbol: bool = True,
        include_header: bool = True,
        separator: str = ",",
        decimal: str = "."
    ) -> str:
        """
        Export data to CSV file.
        
        Args:
            data: DataFrame or list of DataFrames to export
            filename: Output filename
            include_symbol: Include symbol column
            include_header: Include column headers
            separator: Field separator
            decimal: Decimal point character
            
        Returns:
            Full path to exported file
        """
        filepath = self._get_filepath(filename, ".csv")
        
        if isinstance(data, list):
            combined_df = pd.concat(data, ignore_index=True)
        else:
            combined_df = data
        
        export_df = self._prepare_dataframe(combined_df, include_symbol)
        
        export_df.to_csv(
            filepath,
            index=False,
            header=include_header,
            sep=separator,
            decimal=decimal
        )
        
        logger.info(f"Exported {len(export_df)} rows to {filepath}")
        return str(filepath)
    
    def to_excel(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        filename: str,
        sheet_name: str = "Data",
        include_symbol: bool = True,
        auto_column_width: bool = True
    ) -> str:
        """
        Export data to Excel file.
        
        Args:
            data: DataFrame or dict of sheet_name->DataFrame
            filename: Output filename
            sheet_name: Sheet name (if single DataFrame)
            include_symbol: Include symbol column
            auto_column_width: Auto-adjust column widths
            
        Returns:
            Full path to exported file
        """
        filepath = self._get_filepath(filename, ".xlsx")
        
        if isinstance(data, dict):
            sheets = {
                name: self._prepare_dataframe(df, include_symbol) 
                for name, df in data.items()
            }
        else:
            sheets = {sheet_name: self._prepare_dataframe(data, include_symbol)}
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for name, df in sheets.items():
                df.to_excel(writer, sheet_name=name, index=False)
                
                if auto_column_width:
                    worksheet = writer.sheets[name]
                    for idx, col in enumerate(df.columns):
                        max_length = max(
                            df[col].astype(str).map(len).max(),
                            len(str(col))
                        ) + 2
                        worksheet.column_dimensions[
                            chr(65 + idx)
                        ].width = min(max_length, 50)
        
        logger.info(f"Exported to Excel: {filepath}")
        return str(filepath)
    
    def to_json(
        self,
        data: pd.DataFrame,
        filename: str,
        orient: str = "records",
        indent: int = 2,
        include_metadata: bool = True
    ) -> str:
        """
        Export data to JSON file.
        
        Args:
            data: DataFrame to export
            filename: Output filename
            orient: JSON orientation (records, columns, index, etc.)
            indent: JSON indentation
            include_metadata: Include export metadata
            
        Returns:
            Full path to exported file
        """
        filepath = self._get_filepath(filename, ".json")
        
        export_df = self._prepare_dataframe(data)
        
        if include_metadata:
            output = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_records": len(export_df),
                    "columns": list(export_df.columns)
                },
                "data": json.loads(export_df.to_json(orient=orient))
            }
            
            with open(filepath, 'w') as f:
                json.dump(output, f, indent=indent)
        else:
            export_df.to_json(filepath, orient=orient, indent=indent)
        
        logger.info(f"Exported {len(export_df)} rows to JSON: {filepath}")
        return str(filepath)
    
    def to_parquet(
        self,
        data: pd.DataFrame,
        filename: str,
        compression: str = "snappy"
    ) -> str:
        """
        Export data to Parquet file (efficient for large datasets).
        
        Args:
            data: DataFrame to export
            filename: Output filename
            compression: Compression algorithm (snappy, gzip, brotli)
            
        Returns:
            Full path to exported file
        """
        filepath = self._get_filepath(filename, ".parquet")
        
        data.to_parquet(filepath, compression=compression, index=True)
        
        logger.info(f"Exported to Parquet: {filepath}")
        return str(filepath)
    
    def export_multiple(
        self,
        data_dict: Dict[str, pd.DataFrame],
        base_filename: str,
        format: str = "csv"
    ) -> List[str]:
        """
        Export multiple DataFrames to separate files.
        
        Args:
            data_dict: Dictionary of name->DataFrame
            base_filename: Base filename (symbol will be appended)
            format: Export format (csv, excel, json)
            
        Returns:
            List of exported file paths
        """
        exported_files = []
        
        for name, df in data_dict.items():
            filename = f"{base_filename}_{name}"
            
            if format == "csv":
                path = self.to_csv(df, filename)
            elif format == "excel":
                path = self.to_excel(df, filename)
            elif format == "json":
                path = self.to_json(df, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            exported_files.append(path)
        
        return exported_files
    
    def create_summary_report(
        self,
        data: pd.DataFrame,
        filename: str = "summary_report"
    ) -> str:
        """
        Create a summary report with statistics.
        
        Args:
            data: DataFrame to analyze
            filename: Output filename
            
        Returns:
            Path to report file
        """
        filepath = self._get_filepath(filename, ".txt")
        
        report_lines = [
            "=" * 60,
            "MARKET DATA SUMMARY REPORT",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "DATA OVERVIEW",
            "-" * 40,
            f"Total Records: {len(data)}",
            f"Date Range: {data.index.min()} to {data.index.max()}",
            "",
        ]
        
        if 'symbol' in data.columns:
            symbols = data['symbol'].unique()
            report_lines.append(f"Symbols: {', '.join(symbols)}")
            report_lines.append("")
        
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        available_cols = [c for c in numeric_cols if c in data.columns]
        
        if available_cols:
            report_lines.append("PRICE STATISTICS")
            report_lines.append("-" * 40)
            
            for col in available_cols:
                if col == 'volume':
                    report_lines.append(
                        f"Total Volume: {data[col].sum():,.0f}"
                    )
                    report_lines.append(
                        f"Avg Volume: {data[col].mean():,.0f}"
                    )
                else:
                    report_lines.append(
                        f"{col.upper()}: Min={data[col].min():.4f}, "
                        f"Max={data[col].max():.4f}, "
                        f"Mean={data[col].mean():.4f}"
                    )
            
            report_lines.append("")
            
            if 'close' in data.columns and len(data) > 1:
                report_lines.append("PERFORMANCE")
                report_lines.append("-" * 40)
                
                first_close = data['close'].iloc[0]
                last_close = data['close'].iloc[-1]
                pct_change = ((last_close - first_close) / first_close) * 100
                
                report_lines.append(f"First Close: {first_close:.4f}")
                report_lines.append(f"Last Close: {last_close:.4f}")
                report_lines.append(f"Change: {pct_change:+.2f}%")
        
        report_lines.append("")
        report_lines.append("=" * 60)
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"Created summary report: {filepath}")
        return str(filepath)


def quick_export(
    data: pd.DataFrame,
    filename: str,
    format: str = "csv"
) -> str:
    """
    Quick export function for simple use cases.
    
    Args:
        data: DataFrame to export
        filename: Output filename
        format: Export format (csv, excel, json, parquet)
        
    Returns:
        Path to exported file
    """
    exporter = DataExporter()
    
    format_map = {
        "csv": exporter.to_csv,
        "excel": exporter.to_excel,
        "json": exporter.to_json,
        "parquet": exporter.to_parquet
    }
    
    if format not in format_map:
        raise ValueError(f"Unsupported format: {format}")
    
    return format_map[format](data, filename)
