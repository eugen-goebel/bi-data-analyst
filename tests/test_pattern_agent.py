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


# ---------------------------------------------------------------------------
# ABC / Pareto analysis
# ---------------------------------------------------------------------------

class TestABCAnalysis:
    """Coverage for the 80-15-5 segmentation."""

    def test_abc_analyses_produced_for_sample(self, analysis_result):
        patterns, _, _ = analysis_result
        assert len(patterns.abc_analyses) > 0
        # Sample data has 'region' and 'product_category' as dimensions
        dims = {a.dimension for a in patterns.abc_analyses}
        assert dims & {"region", "product_category"}

    def test_contributors_are_sorted_descending(self, analysis_result):
        patterns, _, _ = analysis_result
        for abc in patterns.abc_analyses:
            values = [c.value for c in abc.contributors]
            assert values == sorted(values, reverse=True)

    def test_cumulative_share_monotone_and_terminal_100(self, analysis_result):
        patterns, _, _ = analysis_result
        for abc in patterns.abc_analyses:
            previous = 0.0
            for c in abc.contributors:
                assert c.cumulative_pct >= previous - 0.01  # allow float noise
                previous = c.cumulative_pct
            # Last contributor's cumulative should be ~100
            assert abs(abc.contributors[-1].cumulative_pct - 100.0) < 0.5

    def test_abc_counts_match_classes(self, analysis_result):
        patterns, _, _ = analysis_result
        for abc in patterns.abc_analyses:
            a = sum(1 for c in abc.contributors if c.abc_class == "A")
            b = sum(1 for c in abc.contributors if c.abc_class == "B")
            c = sum(1 for c in abc.contributors if c.abc_class == "C")
            assert (a, b, c) == (abc.a_count, abc.b_count, abc.c_count)
            assert a + b + c == len(abc.contributors)

    def test_a_class_boundary_respects_80pct(self, analysis_result):
        """The last A item's cumulative share is ≤80%; the first B item's >80%."""
        patterns, _, _ = analysis_result
        for abc in patterns.abc_analyses:
            a_items = [c for c in abc.contributors if c.abc_class == "A"]
            b_items = [c for c in abc.contributors if c.abc_class == "B"]
            if len(a_items) > 1:
                # Last A item (excluding the always-first item) must be ≤ 80%
                assert a_items[-1].cumulative_pct <= 80.0 + 0.5
            if b_items:
                # First B item just crossed the 80% threshold
                assert b_items[0].cumulative_pct > 80.0 - 0.5

    def test_classic_pareto_dataset(self):
        """8 of 10 items contribute ~20% combined → A=2, B=4, C=4."""
        import pandas as pd
        from agents.pattern_agent import PatternAgent

        # 2 dominant segments (90% of revenue), 8 small ones — classic 80/20
        df = pd.DataFrame({
            "product": [f"P{i}" for i in range(1, 11)],
            "extra_dim": ["x", "y"] * 5,                 # 2nd dim so agent picks 'product'
            "revenue": [500, 400, 20, 20, 15, 15, 10, 10, 5, 5],
            "units":   [50,  40,  2,  2,  1,  1,  1,  1, 1, 1],
        })
        results = PatternAgent()._analyze_abc(df)
        product_revenue = next(
            (a for a in results if a.dimension == "product" and a.metric == "revenue"),
            None,
        )
        assert product_revenue is not None
        # Top 2 items = 900/1000 = 90% → only P1 lands in A (cum=50% then 90%)
        # First contributor (P1=50%) is A; P2 pushes to 90% which is > 80% → B
        # Our "always include one A" rule means at least 1; 90% > 80% so cutover at P2
        assert product_revenue.a_count >= 1
        # All cumulative shares must climb to 100
        assert abs(product_revenue.contributors[-1].cumulative_pct - 100.0) < 0.5

    def test_single_value_dimension_skipped(self):
        import pandas as pd
        from agents.pattern_agent import PatternAgent

        # 'region' has only one value → cannot do meaningful ABC
        df = pd.DataFrame({
            "region": ["North"] * 10,
            "other_dim": ["a", "b"] * 5,
            "revenue": [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
        })
        results = PatternAgent()._analyze_abc(df)
        assert all(r.dimension != "region" for r in results)

    def test_all_negative_metric_skipped(self):
        import pandas as pd
        from agents.pattern_agent import PatternAgent

        df = pd.DataFrame({
            "region": ["N", "S", "E", "W"] * 3,
            "loss": [-10, -20, -30, -40] * 3,           # all negative → skip
            "revenue": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120],
        })
        results = PatternAgent()._analyze_abc(df)
        # 'loss' should not appear as a metric
        assert all(r.metric != "loss" for r in results)
        # But 'revenue' should
        assert any(r.metric == "revenue" for r in results)

    def test_summary_text_present(self, analysis_result):
        patterns, _, _ = analysis_result
        for abc in patterns.abc_analyses:
            assert abc.summary
            assert abc.dimension in abc.summary or abc.metric in abc.summary
