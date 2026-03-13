"""
Tests for all Pydantic models used across agents.

Covers: ColumnProfile, NumericStats, DataSummary, TrendResult,
CorrelationPair, Outlier, SeasonalPattern, PatternAnalysis,
KeyFinding, Recommendation, InsightResult.
"""

import pytest
from pydantic import ValidationError

from agents.data_loader import ColumnProfile, NumericStats, DataSummary
from agents.pattern_agent import (
    TrendResult, CorrelationPair, Outlier, SeasonalPattern, PatternAnalysis,
)
from agents.insight_agent import KeyFinding, Recommendation, InsightResult


# ---------------------------------------------------------------------------
# ColumnProfile
# ---------------------------------------------------------------------------

class TestColumnProfile:
    def test_valid_column_profile(self):
        cp = ColumnProfile(
            name="revenue",
            dtype="numeric",
            non_null_count=100,
            null_count=0,
            unique_count=95,
            sample_values=["100.5", "200.3", "300.1"],
        )
        assert cp.name == "revenue"
        assert cp.dtype == "numeric"
        assert cp.non_null_count == 100

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            ColumnProfile(
                dtype="numeric",
                non_null_count=100,
                null_count=0,
                unique_count=95,
                sample_values=["1"],
            )

    def test_json_roundtrip(self):
        cp = ColumnProfile(
            name="region",
            dtype="categorical",
            non_null_count=50,
            null_count=2,
            unique_count=4,
            sample_values=["North", "South"],
        )
        data = cp.model_dump_json()
        restored = ColumnProfile.model_validate_json(data)
        assert restored == cp


# ---------------------------------------------------------------------------
# NumericStats
# ---------------------------------------------------------------------------

class TestNumericStats:
    def test_valid_numeric_stats(self):
        ns = NumericStats(
            column="revenue",
            mean=500.0,
            median=480.0,
            std=120.0,
            min=50.0,
            max=1200.0,
            q25=350.0,
            q75=650.0,
        )
        assert ns.column == "revenue"
        assert ns.mean == 500.0

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            NumericStats(
                column="revenue",
                mean=500.0,
                # missing median and others
            )

    def test_json_roundtrip(self):
        ns = NumericStats(
            column="profit",
            mean=200.0,
            median=190.0,
            std=50.0,
            min=10.0,
            max=500.0,
            q25=150.0,
            q75=250.0,
        )
        data = ns.model_dump_json()
        restored = NumericStats.model_validate_json(data)
        assert restored == ns


# ---------------------------------------------------------------------------
# DataSummary
# ---------------------------------------------------------------------------

class TestDataSummary:
    def test_valid_data_summary(self):
        col = ColumnProfile(
            name="x", dtype="numeric", non_null_count=10,
            null_count=0, unique_count=10, sample_values=["1"],
        )
        ds = DataSummary(
            filename="test.csv",
            row_count=100,
            column_count=5,
            columns=[col],
            numeric_stats=[],
            data_quality_score=95.0,
        )
        assert ds.filename == "test.csv"
        assert ds.date_range is None

    def test_missing_columns_raises(self):
        with pytest.raises(ValidationError):
            DataSummary(
                filename="test.csv",
                row_count=100,
                column_count=5,
                # missing columns list
                numeric_stats=[],
                data_quality_score=95.0,
            )


# ---------------------------------------------------------------------------
# TrendResult
# ---------------------------------------------------------------------------

class TestTrendResult:
    def test_valid_trend(self):
        t = TrendResult(
            column="revenue",
            direction="increasing",
            change_pct=15.3,
            description="Revenue increased by 15.3%",
        )
        assert t.direction == "increasing"

    def test_invalid_direction_raises(self):
        with pytest.raises(ValidationError):
            TrendResult(
                column="revenue",
                direction="sideways",  # not a valid Literal value
                change_pct=0.0,
                description="test",
            )


# ---------------------------------------------------------------------------
# CorrelationPair
# ---------------------------------------------------------------------------

class TestCorrelationPair:
    def test_valid_correlation(self):
        cp = CorrelationPair(
            column_a="revenue",
            column_b="customer_count",
            correlation=0.85,
            interpretation="strong positive correlation",
        )
        assert cp.correlation == 0.85

    def test_json_roundtrip(self):
        cp = CorrelationPair(
            column_a="a", column_b="b",
            correlation=-0.72,
            interpretation="negative",
        )
        restored = CorrelationPair.model_validate_json(cp.model_dump_json())
        assert restored == cp


# ---------------------------------------------------------------------------
# Outlier
# ---------------------------------------------------------------------------

class TestOutlier:
    def test_valid_outlier(self):
        o = Outlier(
            column="returns",
            value=89.0,
            row_index=42,
            z_score=4.5,
            description="Unusual returns value",
        )
        assert o.z_score == 4.5

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            Outlier(
                column="returns",
                value=89.0,
                # missing row_index, z_score, description
            )


# ---------------------------------------------------------------------------
# SeasonalPattern
# ---------------------------------------------------------------------------

class TestSeasonalPattern:
    def test_valid_seasonal(self):
        sp = SeasonalPattern(
            column="revenue",
            period="monthly",
            peak_period="December",
            trough_period="February",
            description="Revenue peaks in December",
        )
        assert sp.peak_period == "December"


# ---------------------------------------------------------------------------
# PatternAnalysis
# ---------------------------------------------------------------------------

class TestPatternAnalysis:
    def test_valid_pattern_analysis(self):
        pa = PatternAnalysis(
            trends=[],
            correlations=[],
            outliers=[],
            seasonal_patterns=[],
            summary="No significant patterns detected.",
        )
        assert pa.summary == "No significant patterns detected."

    def test_missing_summary_raises(self):
        with pytest.raises(ValidationError):
            PatternAnalysis(
                trends=[],
                correlations=[],
                outliers=[],
                seasonal_patterns=[],
                # missing summary
            )


# ---------------------------------------------------------------------------
# Recommendation (Literal validation)
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_valid_recommendation(self):
        r = Recommendation(
            title="Increase inventory",
            description="Increase inventory for Q4.",
            priority="High",
            category="Revenue Growth",
            expected_impact="10% revenue increase",
        )
        assert r.priority == "High"
        assert r.category == "Revenue Growth"

    def test_invalid_priority_raises(self):
        with pytest.raises(ValidationError):
            Recommendation(
                title="Test",
                description="Test desc.",
                priority="Critical",  # not in Literal["High", "Medium", "Low"]
                category="Revenue Growth",
                expected_impact="impact",
            )

    def test_invalid_category_raises(self):
        with pytest.raises(ValidationError):
            Recommendation(
                title="Test",
                description="Test desc.",
                priority="High",
                category="Marketing",  # not a valid category
                expected_impact="impact",
            )

    def test_all_valid_priorities(self):
        for p in ["High", "Medium", "Low"]:
            r = Recommendation(
                title="t", description="d", priority=p,
                category="Strategic", expected_impact="e",
            )
            assert r.priority == p

    def test_all_valid_categories(self):
        categories = [
            "Revenue Growth", "Cost Reduction", "Risk Mitigation",
            "Operational Efficiency", "Strategic",
        ]
        for c in categories:
            r = Recommendation(
                title="t", description="d", priority="Low",
                category=c, expected_impact="e",
            )
            assert r.category == c


# ---------------------------------------------------------------------------
# InsightResult
# ---------------------------------------------------------------------------

class TestInsightResult:
    def test_valid_insight_result(self):
        ir = InsightResult(
            executive_summary="Summary text.",
            key_findings=[],
            recommendations=[],
            risk_alerts=["Risk 1"],
            opportunities=["Opp 1"],
            methodology_note="Standard analysis.",
        )
        assert ir.executive_summary == "Summary text."

    def test_missing_executive_summary_raises(self):
        with pytest.raises(ValidationError):
            InsightResult(
                key_findings=[],
                recommendations=[],
                risk_alerts=[],
                opportunities=[],
                methodology_note="note",
            )

    def test_json_roundtrip(self):
        finding = KeyFinding(
            finding="Test finding",
            evidence="Test evidence",
            business_implication="Test implication",
        )
        rec = Recommendation(
            title="t", description="d", priority="High",
            category="Strategic", expected_impact="e",
        )
        ir = InsightResult(
            executive_summary="Summary.",
            key_findings=[finding],
            recommendations=[rec],
            risk_alerts=["r1"],
            opportunities=["o1"],
            methodology_note="method",
        )
        restored = InsightResult.model_validate_json(ir.model_dump_json())
        assert restored == ir
