"""
Tests for the PatternAgent.

Loads sample_sales.csv via DataLoaderAgent first, then runs PatternAgent
on the real data.
"""

import os
import pytest

from agents.data_loader import DataLoaderAgent
from agents.pattern_agent import (
    PatternAgent, PatternAnalysis, TrendResult,
    CorrelationPair, Outlier, SeasonalPattern,
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SAMPLE_CSV = os.path.join(DATA_DIR, "sample_sales.csv")


@pytest.fixture(scope="module")
def analysis_result():
    """Load data and run pattern analysis once for the module."""
    loader = DataLoaderAgent()
    summary, df = loader.load(SAMPLE_CSV)
    agent = PatternAgent()
    patterns = agent.analyze(df, summary)
    return patterns, summary, df


class TestPatternAgent:
    def test_returns_pattern_analysis(self, analysis_result):
        patterns, _, _ = analysis_result
        assert isinstance(patterns, PatternAnalysis)

    def test_trends_detected(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.trends) > 0
        for t in patterns.trends:
            assert isinstance(t, TrendResult)
            assert t.direction in ("increasing", "decreasing", "stable", "volatile")

    def test_correlations_found(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.correlations) > 0
        # revenue and customer_count should be correlated
        col_pairs = {
            (c.column_a, c.column_b) for c in patterns.correlations
        }
        # Check that at least one pair involves revenue and customer_count
        has_rev_cust = any(
            ("customer_count" in pair and "revenue" in pair)
            for pair in [(c.column_a, c.column_b) for c in patterns.correlations]
        )
        assert has_rev_cust, "Expected correlation between revenue and customer_count"

    def test_outliers_found(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.outliers) > 0
        for o in patterns.outliers:
            assert isinstance(o, Outlier)
            assert abs(o.z_score) > 2.5

    def test_returns_outlier_detected(self, analysis_result):
        """The sample data has an anomalous returns value (89)."""
        patterns, _, _ = analysis_result
        returns_outliers = [o for o in patterns.outliers if o.column == "returns"]
        assert len(returns_outliers) > 0, "Expected outlier in returns column"

    def test_seasonal_patterns_detected(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.seasonal_patterns) > 0
        for sp in patterns.seasonal_patterns:
            assert isinstance(sp, SeasonalPattern)
            assert sp.period == "monthly"

    def test_summary_text_nonempty(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.summary) > 0
        assert "found" in patterns.summary.lower() or "no significant" in patterns.summary.lower()

    def test_correlation_values_in_range(self, analysis_result):
        patterns, _, _ = analysis_result
        for c in patterns.correlations:
            assert -1.0 <= c.correlation <= 1.0
            assert abs(c.correlation) > 0.5  # only significant ones
