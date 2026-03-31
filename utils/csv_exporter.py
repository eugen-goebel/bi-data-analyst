"""
CSV Exporter — Exports analysis results as a structured CSV file.

Transforms DataSummary, PatternAnalysis, and InsightResult into
a tabular CSV format for use in spreadsheets or data pipelines.
"""

import csv
import io
import os
from datetime import datetime

from agents.data_loader import DataSummary
from agents.pattern_agent import PatternAnalysis
from agents.insight_agent import InsightResult


def _sanitize_cell(value: str) -> str:
    """Strip leading formula characters to prevent CSV injection."""
    if isinstance(value, str) and value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def export_analysis_csv(
    summary: DataSummary,
    patterns: PatternAnalysis,
    insights: InsightResult,
    output_dir: str = "output",
) -> str:
    """
    Export key metrics, statistical summaries, and insights as a CSV file.

    The CSV contains labeled sections separated by blank rows:
    Overview, Numeric Statistics, Trends, Correlations, Outliers,
    Key Findings, Recommendations, Risk Alerts, Opportunities.

    Args:
        summary:    DataSummary from DataLoaderAgent
        patterns:   PatternAnalysis from PatternAgent
        insights:   InsightResult from InsightAgent
        output_dir: Directory where the file will be saved

    Returns:
        Absolute path to the generated .csv file
    """
    os.makedirs(output_dir, exist_ok=True)

    rows = _build_rows(summary, patterns, insights)

    safe_name = summary.filename.replace(".csv", "").replace(".xlsx", "")
    safe_name = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in safe_name).lower()
    filename = f"bi_export_{safe_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in rows:
            writer.writerow([_sanitize_cell(str(cell)) for cell in row])

    return os.path.abspath(filepath)


def export_analysis_csv_string(
    summary: DataSummary,
    patterns: PatternAnalysis,
    insights: InsightResult,
) -> str:
    """Return the CSV content as a string (useful for APIs or streaming)."""
    rows = _build_rows(summary, patterns, insights)
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        writer.writerow([_sanitize_cell(str(cell)) for cell in row])
    return buf.getvalue()


def _build_rows(
    summary: DataSummary,
    patterns: PatternAnalysis,
    insights: InsightResult,
) -> list[list[str]]:
    """Assemble all CSV rows from the analysis artifacts."""
    rows: list[list[str]] = []

    # --- Overview ---
    rows.append(["Section", "Field", "Value"])
    rows.append(["Overview", "Filename", summary.filename])
    rows.append(["Overview", "Row Count", str(summary.row_count)])
    rows.append(["Overview", "Column Count", str(summary.column_count)])
    rows.append(["Overview", "Date Range", summary.date_range or "N/A"])
    rows.append(["Overview", "Data Quality Score", str(summary.data_quality_score)])
    rows.append([])

    # --- Numeric Statistics ---
    rows.append(["Metric", "Mean", "Median", "Std Dev", "Min", "Max", "Q25", "Q75"])
    for stat in summary.numeric_stats:
        rows.append([
            stat.column, str(stat.mean), str(stat.median), str(stat.std),
            str(stat.min), str(stat.max), str(stat.q25), str(stat.q75),
        ])
    rows.append([])

    # --- Trends ---
    rows.append(["Trend Column", "Direction", "Change %", "Description"])
    for trend in patterns.trends:
        rows.append([
            trend.column, trend.direction,
            str(trend.change_pct), trend.description,
        ])
    rows.append([])

    # --- Correlations ---
    rows.append(["Column A", "Column B", "Correlation", "Interpretation"])
    for corr in patterns.correlations:
        rows.append([
            corr.column_a, corr.column_b,
            str(corr.correlation), corr.interpretation,
        ])
    rows.append([])

    # --- Outliers ---
    rows.append(["Outlier Column", "Value", "Row Index", "Z-Score", "Description"])
    for outlier in patterns.outliers:
        rows.append([
            outlier.column, str(outlier.value), str(outlier.row_index),
            str(outlier.z_score), outlier.description,
        ])
    rows.append([])

    # --- Key Findings ---
    rows.append(["Finding", "Evidence", "Business Implication"])
    for finding in insights.key_findings:
        rows.append([finding.finding, finding.evidence, finding.business_implication])
    rows.append([])

    # --- Recommendations ---
    rows.append(["Title", "Description", "Priority", "Category", "Expected Impact"])
    for rec in insights.recommendations:
        rows.append([
            rec.title, rec.description, rec.priority,
            rec.category, rec.expected_impact,
        ])
    rows.append([])

    # --- Risk Alerts ---
    rows.append(["Risk Alert"])
    for alert in insights.risk_alerts:
        rows.append([alert])
    rows.append([])

    # --- Opportunities ---
    rows.append(["Opportunity"])
    for opp in insights.opportunities:
        rows.append([opp])

    return rows
