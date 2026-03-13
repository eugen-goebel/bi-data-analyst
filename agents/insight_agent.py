"""
Insight Agent — Generates AI-powered business insights and recommendations.

Uses the Anthropic API with structured outputs to transform statistical
patterns into actionable business intelligence.
"""

import anthropic
from pydantic import BaseModel, Field
from typing import Literal

from .data_loader import DataSummary
from .pattern_agent import PatternAnalysis


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class KeyFinding(BaseModel):
    """A data-driven business finding."""
    finding: str = Field(description="One clear data-driven finding")
    evidence: str = Field(description="Specific data point or pattern supporting this")
    business_implication: str = Field(description="What this means for the business")


class Recommendation(BaseModel):
    """An actionable business recommendation."""
    title: str = Field(description="Short action-oriented title")
    description: str = Field(description="2-3 sentence explanation")
    priority: Literal["High", "Medium", "Low"]
    category: Literal[
        "Revenue Growth", "Cost Reduction", "Risk Mitigation",
        "Operational Efficiency", "Strategic"
    ]
    expected_impact: str = Field(description="Estimated business impact")


class InsightResult(BaseModel):
    """Complete AI-generated business insights."""
    executive_summary: str = Field(description="3-4 sentence overview")
    key_findings: list[KeyFinding] = Field(description="Major findings from the data")
    recommendations: list[Recommendation] = Field(description="Actionable recommendations")
    risk_alerts: list[str] = Field(description="Data-driven risk warnings")
    opportunities: list[str] = Field(description="Growth or improvement opportunities")
    methodology_note: str = Field(description="Brief note on analysis performed")


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class InsightAgent:
    """
    Generates business insights by sending data summaries and patterns
    to the Anthropic API, which returns structured recommendations.
    """

    def __init__(self, client: anthropic.Anthropic, model: str = "claude-opus-4-6"):
        self.client = client
        self.model = model

    def generate_insights(
        self, summary: DataSummary, patterns: PatternAnalysis
    ) -> InsightResult:
        """
        Generate AI-powered insights from data analysis results.

        Args:
            summary:  DataSummary from the DataLoaderAgent
            patterns: PatternAnalysis from the PatternAgent

        Returns:
            InsightResult with findings, recommendations, and risks
        """
        system_prompt = (
            "You are a senior business intelligence analyst. Given a dataset summary "
            "and statistical pattern analysis, produce actionable business insights. "
            "Be specific and reference actual numbers from the data. "
            "Provide at least 5 key findings, 5 recommendations (with clear priorities), "
            "4 risk alerts, and 4 opportunities. "
            "Each recommendation must have a concrete expected impact statement."
        )

        # Format data for the prompt
        data_context = self._format_context(summary, patterns)

        response = self.client.messages.parse(
            model=self.model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze the following business data and generate comprehensive "
                        f"insights with actionable recommendations.\n\n{data_context}"
                    ),
                }
            ],
            output_format=InsightResult,
        )

        return response.parsed_output

    def _format_context(self, summary: DataSummary, patterns: PatternAnalysis) -> str:
        """Format DataSummary and PatternAnalysis into a readable prompt."""
        lines = [
            "=== DATASET OVERVIEW ===",
            f"File: {summary.filename}",
            f"Rows: {summary.row_count:,} | Columns: {summary.column_count}",
            f"Date Range: {summary.date_range or 'N/A'}",
            f"Data Quality Score: {summary.data_quality_score}/100",
            "",
            "=== NUMERIC STATISTICS ===",
        ]

        for stat in summary.numeric_stats:
            lines.append(
                f"  {stat.column}: mean={stat.mean:,.1f}, median={stat.median:,.1f}, "
                f"min={stat.min:,.1f}, max={stat.max:,.1f}, std={stat.std:,.1f}"
            )

        lines.append("\n=== DETECTED TRENDS ===")
        for trend in patterns.trends:
            lines.append(f"  {trend.description}")

        lines.append("\n=== CORRELATIONS ===")
        for corr in patterns.correlations:
            lines.append(f"  {corr.interpretation}")

        lines.append("\n=== OUTLIERS ===")
        for outlier in patterns.outliers:
            lines.append(f"  {outlier.description}")

        lines.append("\n=== SEASONAL PATTERNS ===")
        for sp in patterns.seasonal_patterns:
            lines.append(f"  {sp.description}")

        lines.append(f"\n=== PATTERN SUMMARY ===\n{patterns.summary}")

        return "\n".join(lines)
