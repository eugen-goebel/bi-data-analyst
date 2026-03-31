"""Tests for the CSV exporter."""

import csv
import os

from agents.data_loader import DataSummary, ColumnProfile, NumericStats
from agents.pattern_agent import PatternAnalysis, TrendResult, CorrelationPair, Outlier
from agents.insight_agent import InsightResult, KeyFinding, Recommendation
from utils.csv_exporter import export_analysis_csv, export_analysis_csv_string, _sanitize_cell


def _make_summary():
    return DataSummary(
        filename="test_data.csv",
        row_count=100,
        column_count=3,
        columns=[
            ColumnProfile(
                name="revenue", dtype="numeric",
                non_null_count=100, null_count=0,
                unique_count=95, sample_values=["100", "200", "300"],
            ),
        ],
        numeric_stats=[
            NumericStats(
                column="revenue", mean=500.0, median=480.0,
                std=120.0, min=100.0, max=900.0, q25=400.0, q75=600.0,
            ),
        ],
        date_range="2024-01 to 2024-12",
        data_quality_score=92.5,
    )


def _make_patterns():
    return PatternAnalysis(
        trends=[
            TrendResult(
                column="revenue", direction="increasing",
                change_pct=15.3, description="Revenue shows steady growth",
            ),
        ],
        correlations=[
            CorrelationPair(
                column_a="revenue", column_b="orders",
                correlation=0.87, interpretation="Strong positive correlation",
            ),
        ],
        outliers=[
            Outlier(
                column="revenue", value=900.0, row_index=42,
                z_score=3.2, description="Unusually high revenue in row 42",
            ),
        ],
        seasonal_patterns=[],
        summary="Revenue trending upward with strong order correlation.",
    )


def _make_insights():
    return InsightResult(
        executive_summary="Test summary of business data analysis.",
        key_findings=[
            KeyFinding(
                finding="Revenue is growing",
                evidence="15.3% increase over the period",
                business_implication="Positive market momentum",
            ),
        ],
        recommendations=[
            Recommendation(
                title="Increase marketing spend",
                description="Capitalize on growth trend by increasing ad budget.",
                priority="High",
                category="Revenue Growth",
                expected_impact="10-15% additional revenue",
            ),
        ],
        risk_alerts=["Market saturation risk in Q4"],
        opportunities=["Expand into new region"],
        methodology_note="Statistical analysis of 100 records.",
    )


class TestCSVExport:

    def test_generates_csv_file(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        assert os.path.exists(path)
        assert path.endswith(".csv")

    def test_filename_contains_source(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        assert "test_data" in os.path.basename(path)

    def test_file_not_empty(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        assert os.path.getsize(path) > 100

    def test_csv_is_parseable(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) > 10

    def test_contains_overview_section(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "test_data.csv" in content
        assert "100" in content
        assert "92.5" in content

    def test_contains_statistics(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "revenue" in content
        assert "500.0" in content

    def test_contains_recommendations(self, tmp_path):
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=str(tmp_path),
        )
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "Increase marketing spend" in content

    def test_creates_output_directory(self, tmp_path):
        new_dir = str(tmp_path / "subdir" / "exports")
        path = export_analysis_csv(
            _make_summary(), _make_patterns(), _make_insights(),
            output_dir=new_dir,
        )
        assert os.path.exists(path)
        assert os.path.isdir(new_dir)


class TestCSVString:

    def test_returns_string(self):
        result = export_analysis_csv_string(
            _make_summary(), _make_patterns(), _make_insights(),
        )
        assert isinstance(result, str)
        assert len(result) > 100

    def test_string_contains_data(self):
        result = export_analysis_csv_string(
            _make_summary(), _make_patterns(), _make_insights(),
        )
        assert "revenue" in result
        assert "test_data.csv" in result


class TestSanitization:

    def test_formula_injection_blocked(self):
        assert _sanitize_cell("=SUM(A1)") == "'=SUM(A1)"
        assert _sanitize_cell("+cmd") == "'+cmd"
        assert _sanitize_cell("-1") == "'-1"
        assert _sanitize_cell("@import") == "'@import"

    def test_normal_text_unchanged(self):
        assert _sanitize_cell("Hello") == "Hello"
        assert _sanitize_cell("123") == "123"
        assert _sanitize_cell("") == ""
