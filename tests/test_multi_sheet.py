"""Tests for multi-sheet Excel support in DataLoaderAgent."""

import pytest
import pandas as pd

from agents.data_loader import DataLoaderAgent, DataSummary


@pytest.fixture
def loader():
    return DataLoaderAgent()


@pytest.fixture
def multi_sheet_excel(tmp_path):
    """Create a multi-sheet Excel file for testing."""
    filepath = tmp_path / "multi_sheet.xlsx"
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        pd.DataFrame({
            "product": ["A", "B", "C"],
            "revenue": [100, 200, 300],
            "cost": [50, 100, 150],
        }).to_excel(writer, sheet_name="Sales", index=False)

        pd.DataFrame({
            "name": ["Alice", "Bob"],
            "region": ["North", "South"],
            "score": [85, 92],
        }).to_excel(writer, sheet_name="Customers", index=False)

        # Empty sheet (header only, one column)
        pd.DataFrame({"x": pd.Series(dtype="float")}).to_excel(
            writer, sheet_name="Empty", index=False
        )
    return str(filepath)


@pytest.fixture
def single_sheet_excel(tmp_path):
    """Create a single-sheet Excel file."""
    filepath = tmp_path / "single.xlsx"
    pd.DataFrame({
        "item": ["X", "Y"],
        "value": [10, 20],
    }).to_excel(filepath, index=False, sheet_name="Data")
    return str(filepath)


class TestListSheets:
    def test_list_sheets_returns_names(self, loader, multi_sheet_excel):
        sheets = loader.list_sheets(multi_sheet_excel)
        assert sheets == ["Sales", "Customers", "Empty"]

    def test_list_sheets_single(self, loader, single_sheet_excel):
        sheets = loader.list_sheets(single_sheet_excel)
        assert sheets == ["Data"]

    def test_list_sheets_file_not_found(self, loader):
        with pytest.raises(FileNotFoundError):
            loader.list_sheets("/nonexistent/file.xlsx")

    def test_list_sheets_csv_raises(self, loader, tmp_path):
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b\n1,2\n")
        with pytest.raises(ValueError, match="Excel"):
            loader.list_sheets(str(csv_file))


class TestLoadSpecificSheet:
    def test_load_named_sheet(self, loader, multi_sheet_excel):
        summary, df = loader.load(multi_sheet_excel, sheet_name="Customers")
        assert summary.sheet_name == "Customers"
        assert summary.row_count == 2
        assert "name" in df.columns

    def test_load_first_sheet_by_default(self, loader, multi_sheet_excel):
        summary, df = loader.load(multi_sheet_excel)
        assert summary.row_count == 3
        assert "product" in df.columns

    def test_sheet_name_none_for_csv(self, loader):
        import os
        sample = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "sample_sales.csv",
        )
        summary, _ = loader.load(sample)
        assert summary.sheet_name is None


class TestLoadAllSheets:
    def test_load_all_returns_non_empty_only(self, loader, multi_sheet_excel):
        results = loader.load_all_sheets(multi_sheet_excel)
        # Empty sheet should be skipped
        assert len(results) == 2
        sheet_names = [s.sheet_name for s, _ in results]
        assert "Sales" in sheet_names
        assert "Customers" in sheet_names

    def test_load_all_raises_if_all_empty(self, loader, tmp_path):
        filepath = tmp_path / "empty_sheets.xlsx"
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            pd.DataFrame({"x": pd.Series(dtype="float")}).to_excel(
                writer, sheet_name="Sheet1", index=False
            )
        with pytest.raises(ValueError, match="empty"):
            loader.load_all_sheets(str(filepath))

    def test_each_sheet_has_correct_profile(self, loader, multi_sheet_excel):
        results = loader.load_all_sheets(multi_sheet_excel)
        for summary, df in results:
            assert summary.row_count == len(df)
            assert summary.column_count == len(df.columns)
            assert 0 <= summary.data_quality_score <= 100
