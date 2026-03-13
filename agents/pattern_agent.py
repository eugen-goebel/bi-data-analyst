"""
Pattern Agent — Detects trends, correlations, outliers, and seasonality.

Performs statistical analysis on the dataset using pandas and numpy.
No API call required.
"""

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from typing import Literal

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


class PatternAnalysis(BaseModel):
    """Complete pattern analysis results."""
    trends: list[TrendResult]
    correlations: list[CorrelationPair]
    outliers: list[Outlier]
    seasonal_patterns: list[SeasonalPattern]
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

        summary_text = f"Analysis found {', '.join(parts)}." if parts else "No significant patterns detected."

        return PatternAnalysis(
            trends=trends,
            correlations=correlations,
            outliers=outliers,
            seasonal_patterns=seasonal,
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

            description = f"{col} changed by {change_pct:+.1f}% over the analysis period ({direction})"

            trends.append(TrendResult(
                column=col,
                direction=direction,
                change_pct=change_pct,
                description=description,
            ))

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
                    pairs.append(CorrelationPair(
                        column_a=col_a,
                        column_b=col_b,
                        correlation=round(float(r), 3),
                        interpretation=interpretation,
                    ))

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
                    outliers.append(Outlier(
                        column=col,
                        value=round(float(df.loc[idx, col]), 2),
                        row_index=int(idx),
                        z_score=round(float(z), 2),
                        description=f"Unusual {col} value of {df.loc[idx, col]:.0f} (z-score: {z:.1f})",
                    ))

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

            month_names = {1: "January", 2: "February", 3: "March", 4: "April",
                          5: "May", 6: "June", 7: "July", 8: "August",
                          9: "September", 10: "October", 11: "November", 12: "December"}

            variation = (monthly.max() - monthly.min()) / monthly.mean() if monthly.mean() > 0 else 0
            if variation > 0.15:  # At least 15% variation to count as seasonal
                patterns.append(SeasonalPattern(
                    column=col,
                    period="monthly",
                    peak_period=month_names.get(peak_month, str(peak_month)),
                    trough_period=month_names.get(trough_month, str(trough_month)),
                    description=f"{col} shows seasonal variation of {variation:.0%}, "
                                f"peaking in {month_names.get(peak_month, str(peak_month))}",
                ))

        return patterns
