"""
Data Loader Agent — Reads, validates, and profiles business data files.

Supports CSV and Excel formats. Produces a structured DataSummary with
column profiles, numeric statistics, and a data quality score.
"""

import os
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ColumnProfile(BaseModel):
    """Profile of a single column in the dataset."""
    name: str = Field(description="Column name")
    dtype: str = Field(description="Data type: numeric, categorical, datetime")
    non_null_count: int = Field(description="Number of non-null values")
    null_count: int = Field(description="Number of missing values")
    unique_count: int = Field(description="Number of unique values")
    sample_values: list[str] = Field(description="Up to 5 representative values")


class NumericStats(BaseModel):
    """Descriptive statistics for a numeric column."""
    column: str
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float


class DataSummary(BaseModel):
    """Complete summary of a loaded dataset."""
    filename: str = Field(description="Original filename")
    row_count: int = Field(description="Total number of rows")
    column_count: int = Field(description="Total number of columns")
    columns: list[ColumnProfile] = Field(description="Profile of each column")
    numeric_stats: list[NumericStats] = Field(description="Stats for numeric columns")
    date_range: str | None = Field(default=None, description="Date range if applicable")
    data_quality_score: float = Field(description="0-100 quality score")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class DataLoaderAgent:
    """
    Loads CSV or Excel files, validates the data, computes column profiles
    and descriptive statistics. No API call required.
    """

    SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")

    def load(self, filepath: str) -> tuple[DataSummary, pd.DataFrame]:
        """
        Load and profile a data file.

        Args:
            filepath: Path to a CSV or Excel file

        Returns:
            Tuple of (DataSummary, pandas DataFrame)

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is unsupported or data is empty
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}. Use CSV or Excel.")

        # Read file
        if ext == ".csv":
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)

        if df.empty or len(df.columns) < 2:
            raise ValueError("Dataset is empty or has fewer than 2 columns.")

        # Auto-detect date columns
        for col in df.select_dtypes(include=["object", "string"]).columns:
            try:
                parsed = pd.to_datetime(df[col], format="mixed")
                df[col] = parsed
            except (ValueError, TypeError):
                pass

        # Build column profiles
        columns = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                dtype = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                dtype = "datetime"
            else:
                dtype = "categorical"

            sample = df[col].dropna().head(5).astype(str).tolist()
            columns.append(ColumnProfile(
                name=col,
                dtype=dtype,
                non_null_count=int(df[col].notna().sum()),
                null_count=int(df[col].isna().sum()),
                unique_count=int(df[col].nunique()),
                sample_values=sample,
            ))

        # Numeric statistics
        numeric_stats = []
        for col in df.select_dtypes(include=[np.number]).columns:
            desc = df[col].describe()
            numeric_stats.append(NumericStats(
                column=col,
                mean=round(float(desc["mean"]), 2),
                median=round(float(df[col].median()), 2),
                std=round(float(desc["std"]), 2),
                min=round(float(desc["min"]), 2),
                max=round(float(desc["max"]), 2),
                q25=round(float(desc["25%"]), 2),
                q75=round(float(desc["75%"]), 2),
            ))

        # Date range
        date_range = None
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        if len(date_cols) > 0:
            dt_col = df[date_cols[0]]
            date_range = f"{dt_col.min().strftime('%Y-%m-%d')} to {dt_col.max().strftime('%Y-%m-%d')}"

        # Data quality score (0-100)
        total_cells = df.shape[0] * df.shape[1]
        null_cells = int(df.isnull().sum().sum())
        completeness = (1 - null_cells / total_cells) * 100 if total_cells > 0 else 0
        data_quality_score = round(min(completeness, 100), 1)

        summary = DataSummary(
            filename=os.path.basename(filepath),
            row_count=len(df),
            column_count=len(df.columns),
            columns=columns,
            numeric_stats=numeric_stats,
            date_range=date_range,
            data_quality_score=data_quality_score,
        )

        return summary, df
