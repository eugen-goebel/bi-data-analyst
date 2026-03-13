"""
Tests for the DataLoaderAgent.

Uses the real sample_sales.csv (192 rows, 10 columns) from the data/ directory.
"""

import os
import pytest

from agents.data_loader import DataLoaderAgent, DataSummary

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SAMPLE_CSV = os.path.join(DATA_DIR, "sample_sales.csv")


@pytest.fixture
def loader():
    return DataLoaderAgent()


@pytest.fixture
def loaded_data(loader):
    """Load sample_sales.csv once and reuse."""
    return loader.load(SAMPLE_CSV)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestDataLoaderHappyPath:
    def test_load_returns_tuple(self, loaded_data):
        summary, df = loaded_data
        assert isinstance(summary, DataSummary)
        assert df is not None

    def test_correct_row_count(self, loaded_data):
        summary, df = loaded_data
        assert summary.row_count == 192
        assert len(df) == 192

    def test_correct_column_count(self, loaded_data):
        summary, df = loaded_data
        assert summary.column_count == 10
        assert len(df.columns) == 10

    def test_date_column_detected(self, loaded_data):
        summary, _ = loaded_data
        date_cols = [c for c in summary.columns if c.dtype == "datetime"]
        assert len(date_cols) >= 1, "At least one date column should be detected"
        assert date_cols[0].name == "date"

    def test_date_range_populated(self, loaded_data):
        summary, _ = loaded_data
        assert summary.date_range is not None
        assert "to" in summary.date_range

    def test_numeric_stats_present(self, loaded_data):
        summary, _ = loaded_data
        assert len(summary.numeric_stats) > 0
        stat_columns = {s.column for s in summary.numeric_stats}
        assert "revenue" in stat_columns
        assert "profit" in stat_columns

    def test_data_quality_score_range(self, loaded_data):
        summary, _ = loaded_data
        assert 0 <= summary.data_quality_score <= 100

    def test_filename_is_basename(self, loaded_data):
        summary, _ = loaded_data
        assert summary.filename == "sample_sales.csv"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestDataLoaderErrors:
    def test_file_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.load("/nonexistent/path/data.csv")

    def test_unsupported_format(self, loader, tmp_path):
        bad_file = tmp_path / "data.json"
        bad_file.write_text('{"a": 1}')
        with pytest.raises(ValueError, match="Unsupported file format"):
            loader.load(str(bad_file))

    def test_empty_csv(self, loader, tmp_path):
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("col1\n")  # header only, one column (< 2)
        with pytest.raises(ValueError, match="empty|fewer than 2"):
            loader.load(str(empty_file))
