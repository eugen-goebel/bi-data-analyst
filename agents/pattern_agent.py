"""
Pattern Agent — Detects trends, correlations, outliers, and seasonality.

Performs statistical analysis on the dataset using pandas and numpy.
No API call required.
"""

from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from .data_loader import DataSummary

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TrendResult(BaseModel):
    """Detected trend in a numeric column."""

    column: str = Field(description="Column analyzed")
    direction: Literal["increasing", "decreasing", "stable", "volatile"]
    change_pct: float = Field(description="Percentage change over the period")
    description: str = Field(description="One-sentence trend description")


class CorrelationPair(BaseModel):
    """Significant correlation between two columns."""

    column_a: str
    column_b: str
    correlation: float = Field(description="Pearson correlation coefficient")
    interpretation: str = Field(description="Business interpretation")


class Outlier(BaseModel):
    """Detected statistical outlier."""

    column: str
    value: float
    row_index: int
    z_score: float
    description: str = Field(description="Contextual explanation")


class SeasonalPattern(BaseModel):
    """Detected seasonal or cyclic pattern."""

    column: str
    period: str = Field(description="e.g., monthly, quarterly")
    peak_period: str = Field(description="When the metric typically peaks")
    trough_period: str = Field(description="When the metric typically dips")
    description: str


class ABCContributor(BaseModel):
    """A single segment in an ABC/Pareto analysis."""

    label: str = Field(description="Segment label, e.g. 'North'")
    value: float = Field(description="Contribution in the chosen metric")
    share_pct: float = Field(description="Share of the total in percent")
    cumulative_pct: float = Field(description="Running cumulative share in percent")
    abc_class: Literal["A", "B", "C"] = Field(description="Pareto class")


class ABCAnalysis(BaseModel):
    """Pareto / 80-20 split for one categorical dimension over one numeric metric."""

    dimension: str = Field(description="Categorical column grouped by")
    metric: str = Field(description="Numeric column aggregated")
    total: float = Field(description="Total sum of the metric across all segments")
    contributors: list[ABCContributor]
    a_count: int = Field(description="Segments in the 80% bucket")
    b_count: int = Field(description="Segments in the next 15%")
    c_count: int = Field(description="Segments in the last 5%")
    summary: str


class PatternAnalysis(BaseModel):
    """Complete pattern analysis results."""

    trends: list[TrendResult]
    correlations: list[CorrelationPair]
    outliers: list[Outlier]
    seasonal_patterns: list[SeasonalPattern]
    abc_analyses: list[ABCAnalysis] = Field(default_factory=list)
    summary: str = Field(description="Overview of key patterns found")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class PatternAgent:
    """
    Detects statistical patterns in business data. Analyzes trends,
    correlations, outliers, and seasonality using pandas and numpy.
    No API call required.
    """

    def analyze(self, df: pd.DataFrame, summary: DataSummary) -> PatternAnalysis:
        """
        Run pattern detection on the dataset.

        Args:
            df:      pandas DataFrame with the loaded data
            summary: DataSummary from the DataLoaderAgent

        Returns:
            PatternAnalysis with detected patterns
        """
        trends = self._detect_trends(df, summary)
        correlations = self._find_correlations(df)
        outliers = self._detect_outliers(df)
        seasonal = self._detect_seasonality(df, summary)
        abc_analyses = self._analyze_abc(df)

        # Build summary sentence
        parts = []
        if trends:
            inc = sum(1 for t in trends if t.direction == "increasing")
            dec = sum(1 for t in trends if t.direction == "decreasing")
            if inc:
                parts.append(f"{inc} increasing trend(s)")
            if dec:
                parts.append(f"{dec} decreasing trend(s)")
        if correlations:
            parts.append(f"{len(correlations)} significant correlation(s)")
        if outliers:
            parts.append(f"{len(outliers)} outlier(s)")
        if seasonal:
            parts.append(f"{len(seasonal)} seasonal pattern(s)")
        if abc_analyses:
            parts.append(f"{len(abc_analyses)} ABC/Pareto analyses")

        summary_text = (
            f"Analysis found {', '.join(parts)}." if parts else "No significant patterns detected."
        )

        return PatternAnalysis(
            trends=trends,
            correlations=correlations,
            outliers=outliers,
            seasonal_patterns=seasonal,
            abc_analyses=abc_analyses,
            summary=summary_text,
        )

    def _detect_trends(self, df: pd.DataFrame, summary: DataSummary) -> list[TrendResult]:
        """Detect trends in numeric columns over time."""
        trends = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime64"]).columns

        if len(date_cols) == 0 or len(numeric_cols) == 0:
            return trends

        date_col = date_cols[0]
        monthly = df.groupby(df[date_col].dt.to_period("M"))[numeric_cols].mean()

        if len(monthly) < 2:
            return trends

        for col in numeric_cols:
            first_val = monthly[col].iloc[0]
            last_val = monthly[col].iloc[-1]

            if first_val == 0:
                continue

            change_pct = round(((last_val - first_val) / abs(first_val)) * 100, 1)
            cv = monthly[col].std() / monthly[col].mean() if monthly[col].mean() != 0 else 0

            if cv > 0.3:
                direction = "volatile"
            elif change_pct > 10:
                direction = "increasing"
            elif change_pct < -10:
                direction = "decreasing"
            else:
                direction = "stable"

            description = (
                f"{col} changed by {change_pct:+.1f}% over the analysis period ({direction})"
            )

            trends.append(
                TrendResult(
                    column=col,
                    direction=direction,
                    change_pct=change_pct,
                    description=description,
                )
            )

        return trends

    def _find_correlations(self, df: pd.DataFrame) -> list[CorrelationPair]:
        """Find significant correlations between numeric columns."""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return []

        corr_matrix = numeric_df.corr()
        pairs = []
        seen = set()

        for col_a in corr_matrix.columns:
            for col_b in corr_matrix.columns:
                if col_a >= col_b:
                    continue
                key = (col_a, col_b)
                if key in seen:
                    continue
                seen.add(key)

                r = corr_matrix.loc[col_a, col_b]
                if abs(r) > 0.5 and not np.isnan(r):
                    strength = "strong" if abs(r) > 0.7 else "moderate"
                    direction = "positive" if r > 0 else "negative"
                    interpretation = (
                        f"{strength} {direction} correlation (r={r:.2f}): "
                        f"as {col_a} increases, {col_b} {'increases' if r > 0 else 'decreases'}"
                    )
                    pairs.append(
                        CorrelationPair(
                            column_a=col_a,
                            column_b=col_b,
                            correlation=round(float(r), 3),
                            interpretation=interpretation,
                        )
                    )

        # Sort by absolute correlation strength
        pairs.sort(key=lambda p: abs(p.correlation), reverse=True)
        return pairs[:10]  # Top 10

    def _detect_outliers(self, df: pd.DataFrame) -> list[Outlier]:
        """Detect outliers using z-score method."""
        outliers = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            values = df[col].dropna()
            if len(values) < 10:
                continue

            mean = values.mean()
            std = values.std()
            if std == 0:
                continue

            z_scores = (values - mean) / std

            for idx, z in z_scores.items():
                if abs(z) > 2.5:
                    outliers.append(
                        Outlier(
                            column=col,
                            value=round(float(df.loc[idx, col]), 2),
                            row_index=int(idx),
                            z_score=round(float(z), 2),
                            description=f"Unusual {col} value of {df.loc[idx, col]:.0f} (z-score: {z:.1f})",
                        )
                    )

        outliers.sort(key=lambda o: abs(o.z_score), reverse=True)
        return outliers[:15]  # Top 15

    def _detect_seasonality(self, df: pd.DataFrame, summary: DataSummary) -> list[SeasonalPattern]:
        """Detect seasonal patterns in time-series data."""
        patterns = []
        date_cols = df.select_dtypes(include=["datetime64"]).columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(date_cols) == 0:
            return patterns

        date_col = date_cols[0]
        key_metrics = [c for c in ["revenue", "units_sold", "profit"] if c in numeric_cols]

        if not key_metrics:
            key_metrics = list(numeric_cols[:3])

        for col in key_metrics:
            monthly = df.groupby(df[date_col].dt.month)[col].mean()
            if len(monthly) < 4:
                continue

            peak_month = int(monthly.idxmax())
            trough_month = int(monthly.idxmin())

            month_names = {
                1: "January",
                2: "February",
                3: "March",
                4: "April",
                5: "May",
                6: "June",
                7: "July",
                8: "August",
                9: "September",
                10: "October",
                11: "November",
                12: "December",
            }

            variation = (
                (monthly.max() - monthly.min()) / monthly.mean() if monthly.mean() > 0 else 0
            )
            if variation > 0.15:  # At least 15% variation to count as seasonal
                patterns.append(
                    SeasonalPattern(
                        column=col,
                        period="monthly",
                        peak_period=month_names.get(peak_month, str(peak_month)),
                        trough_period=month_names.get(trough_month, str(trough_month)),
                        description=f"{col} shows seasonal variation of {variation:.0%}, "
                        f"peaking in {month_names.get(peak_month, str(peak_month))}",
                    )
                )

        return patterns

    # ------------------------------------------------------------------
    # ABC / Pareto analysis
    # ------------------------------------------------------------------

    MAX_ABC_DIMENSIONS = 3  # categorical columns to explore
    MAX_ABC_METRICS = 2  # numeric metrics to explore per dimension
    MAX_ABC_CONTRIBUTORS = 50  # rows kept per analysis in the result
    A_THRESHOLD_PCT = 80.0  # cumulative % bound for class A
    B_THRESHOLD_PCT = 95.0  # cumulative % bound for class B

    def _analyze_abc(self, df: pd.DataFrame) -> list[ABCAnalysis]:
        """Classify segments into A/B/C contributors for the 80-20 rule.

        For each candidate (categorical dimension, numeric metric) pair the
        method groups by the dimension, sums the metric, sorts descending
        and tags each segment with its Pareto class based on cumulative
        share.
        """
        # --- 1. Find candidate dimensions: any non-numeric, non-datetime
        # column with 2-100 unique values (skip IDs and free-text). Using
        # the pandas type helpers makes this robust across the object /
        # string / category dtype variants.
        cat_cols: list[str] = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                continue
            uniques = df[col].nunique(dropna=True)
            if 2 <= uniques <= 100:
                cat_cols.append(col)
        cat_cols = cat_cols[: self.MAX_ABC_DIMENSIONS]

        # --- 2. Find candidate metrics: numeric columns with positive total
        # and at least 5 distinct values (skip flags / constants / IDs)
        metric_cols: list[str] = []
        for col in df.select_dtypes(include=[np.number]).columns:
            series = df[col].dropna()
            if len(series) == 0:
                continue
            if series.sum() <= 0:
                continue
            if series.nunique() < 5:
                continue
            metric_cols.append(col)
        metric_cols = metric_cols[: self.MAX_ABC_METRICS]

        if not cat_cols or not metric_cols:
            return []

        analyses: list[ABCAnalysis] = []
        for dim in cat_cols:
            for metric in metric_cols:
                analysis = self._build_abc(df, dim, metric)
                if analysis is not None:
                    analyses.append(analysis)

        return analyses

    def _build_abc(
        self,
        df: pd.DataFrame,
        dim: str,
        metric: str,
    ) -> ABCAnalysis | None:
        """Run the ABC computation for a single (dim, metric) pair."""
        grouped = df.groupby(dim, dropna=True)[metric].sum().sort_values(ascending=False)
        # Drop zero/negative segments — they distort the cumulative share
        grouped = grouped[grouped > 0]
        if len(grouped) < 2:
            return None

        total = float(grouped.sum())
        if total <= 0:
            return None

        contributors: list[ABCContributor] = []
        a_count = b_count = c_count = 0
        cumulative = 0.0

        for label, value in grouped.items():
            share = (float(value) / total) * 100
            cumulative += share

            if cumulative <= self.A_THRESHOLD_PCT or a_count == 0:
                # Always include at least one A segment so a single dominant
                # value is not pushed into B by floating-point noise.
                cls = "A"
                a_count += 1
            elif cumulative <= self.B_THRESHOLD_PCT:
                cls = "B"
                b_count += 1
            else:
                cls = "C"
                c_count += 1

            contributors.append(
                ABCContributor(
                    label=str(label),
                    value=round(float(value), 2),
                    share_pct=round(share, 2),
                    cumulative_pct=round(cumulative, 2),
                    abc_class=cls,
                )
            )

        a_pct = (a_count / len(grouped)) * 100 if grouped.size else 0
        summary = (
            f"{a_count} of {len(grouped)} {dim} segments ({a_pct:.0f}%) drive "
            f"the top {self.A_THRESHOLD_PCT:.0f}% of {metric}"
        )

        return ABCAnalysis(
            dimension=dim,
            metric=metric,
            total=round(total, 2),
            contributors=contributors[: self.MAX_ABC_CONTRIBUTORS],
            a_count=a_count,
            b_count=b_count,
            c_count=c_count,
            summary=summary,
        )
