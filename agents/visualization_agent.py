"""
Visualization Agent — Creates professional charts from business data.

Generates matplotlib charts (line, bar, pie, heatmap, scatter) and saves
them as PNG files for embedding in the DOCX report. No API call required.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from typing import Literal

from .data_loader import DataSummary
from .pattern_agent import PatternAnalysis


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChartConfig(BaseModel):
    """Metadata for a generated chart."""
    chart_type: Literal["bar", "line", "pie", "heatmap", "scatter"]
    title: str
    filename: str = Field(description="Output filename like 'revenue_trend.png'")
    description: str = Field(description="Caption for the report")


class VisualizationResult(BaseModel):
    """Result containing chart metadata and output directory."""
    charts: list[ChartConfig]
    chart_dir: str = Field(description="Directory with generated chart PNGs")


# ---------------------------------------------------------------------------
# Color palette (matches DOCX orange/teal theme)
# ---------------------------------------------------------------------------
COLORS = ["#0D7377", "#C44900", "#2E86AB", "#A23B72", "#F18F01", "#4A7C59"]
BG_COLOR = "#FAFAFA"
GRID_COLOR = "#E0E0E0"


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class VisualizationAgent:
    """
    Creates data visualizations using matplotlib. Automatically selects
    the most meaningful charts based on the dataset structure.
    No API call required.
    """

    def create_charts(
        self,
        df: pd.DataFrame,
        summary: DataSummary,
        patterns: PatternAnalysis,
        output_dir: str,
    ) -> VisualizationResult:
        """
        Generate charts from the data and save as PNG files.

        Args:
            df:         pandas DataFrame with loaded data
            summary:    DataSummary from DataLoaderAgent
            patterns:   PatternAnalysis from PatternAgent
            output_dir: Directory to save chart PNGs

        Returns:
            VisualizationResult with chart metadata
        """
        os.makedirs(output_dir, exist_ok=True)
        charts: list[ChartConfig] = []

        # Identify column types
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns.tolist()

        # Identify key metric (revenue > profit > units_sold > first numeric)
        key_metric = None
        for candidate in ["revenue", "profit", "units_sold"]:
            if candidate in numeric_cols:
                key_metric = candidate
                break
        if key_metric is None and numeric_cols:
            key_metric = numeric_cols[0]

        # 1. Trend line chart (if date column exists)
        if date_cols and key_metric:
            chart = self._create_trend_chart(df, date_cols[0], key_metric, output_dir)
            if chart:
                charts.append(chart)

        # 2. Category breakdown bar chart
        if cat_cols and key_metric:
            chart = self._create_bar_chart(df, cat_cols[0], key_metric, output_dir)
            if chart:
                charts.append(chart)

        # 3. Pie chart (second categorical or same)
        if cat_cols and key_metric:
            cat_col = cat_cols[1] if len(cat_cols) > 1 else cat_cols[0]
            chart = self._create_pie_chart(df, cat_col, key_metric, output_dir)
            if chart:
                charts.append(chart)

        # 4. Correlation heatmap
        if len(numeric_cols) >= 3:
            chart = self._create_heatmap(df, numeric_cols, output_dir)
            if chart:
                charts.append(chart)

        # 5. Scatter plot (if we have two good numeric columns)
        if len(numeric_cols) >= 2 and cat_cols:
            col_x = "customer_count" if "customer_count" in numeric_cols else numeric_cols[0]
            col_y = key_metric if key_metric != col_x else numeric_cols[1]
            chart = self._create_scatter(df, col_x, col_y, cat_cols[0], output_dir)
            if chart:
                charts.append(chart)

        return VisualizationResult(charts=charts, chart_dir=output_dir)

    def _create_trend_chart(self, df, date_col, metric, output_dir) -> ChartConfig | None:
        """Monthly trend line chart."""
        try:
            monthly = df.groupby(df[date_col].dt.to_period("M"))[metric].sum()
            monthly.index = monthly.index.to_timestamp()

            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            ax.plot(monthly.index, monthly.values, color=COLORS[0], linewidth=2.5, marker="o", markersize=6)
            ax.fill_between(monthly.index, monthly.values, alpha=0.1, color=COLORS[0])

            ax.set_title(f"{metric.replace('_', ' ').title()} — Monthly Trend", fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel("")
            ax.set_ylabel(metric.replace("_", " ").title(), fontsize=11)
            ax.grid(True, alpha=0.3, color=GRID_COLOR)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.xticks(rotation=45)
            plt.tight_layout()

            filename = f"{metric}_trend.png"
            fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches="tight")
            plt.close(fig)

            return ChartConfig(
                chart_type="line",
                title=f"{metric.replace('_', ' ').title()} Trend",
                filename=filename,
                description=f"Monthly {metric.replace('_', ' ')} trend over the analysis period",
            )
        except Exception:
            return None

    def _create_bar_chart(self, df, cat_col, metric, output_dir) -> ChartConfig | None:
        """Grouped bar chart by category."""
        try:
            grouped = df.groupby(cat_col)[metric].sum().sort_values(ascending=True)

            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            bars = ax.barh(grouped.index, grouped.values, color=COLORS[:len(grouped)], height=0.6)

            ax.set_title(f"{metric.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                         fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(metric.replace("_", " ").title(), fontsize=11)
            ax.grid(True, axis="x", alpha=0.3, color=GRID_COLOR)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            # Value labels
            for bar in bars:
                width = bar.get_width()
                ax.text(width * 1.01, bar.get_y() + bar.get_height() / 2,
                        f"{width:,.0f}", va="center", fontsize=9, color="#555")

            plt.tight_layout()

            filename = f"{metric}_by_{cat_col}.png"
            fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches="tight")
            plt.close(fig)

            return ChartConfig(
                chart_type="bar",
                title=f"{metric.replace('_', ' ').title()} by {cat_col.replace('_', ' ').title()}",
                filename=filename,
                description=f"Total {metric.replace('_', ' ')} broken down by {cat_col.replace('_', ' ')}",
            )
        except Exception:
            return None

    def _create_pie_chart(self, df, cat_col, metric, output_dir) -> ChartConfig | None:
        """Pie chart showing distribution."""
        try:
            grouped = df.groupby(cat_col)[metric].sum()

            fig, ax = plt.subplots(figsize=(8, 6))
            fig.patch.set_facecolor(BG_COLOR)

            wedges, texts, autotexts = ax.pie(
                grouped.values, labels=grouped.index, autopct="%1.1f%%",
                colors=COLORS[:len(grouped)], startangle=90,
                textprops={"fontsize": 10},
            )
            for autotext in autotexts:
                autotext.set_fontweight("bold")
                autotext.set_color("white")

            ax.set_title(f"{metric.replace('_', ' ').title()} Distribution by {cat_col.replace('_', ' ').title()}",
                         fontsize=14, fontweight="bold", pad=20)

            plt.tight_layout()

            filename = f"{metric}_distribution_{cat_col}.png"
            fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches="tight")
            plt.close(fig)

            return ChartConfig(
                chart_type="pie",
                title=f"{metric.replace('_', ' ').title()} Distribution",
                filename=filename,
                description=f"Share of {metric.replace('_', ' ')} across {cat_col.replace('_', ' ')} categories",
            )
        except Exception:
            return None

    def _create_heatmap(self, df, numeric_cols, output_dir) -> ChartConfig | None:
        """Correlation heatmap of numeric columns."""
        try:
            corr = df[numeric_cols].corr()

            fig, ax = plt.subplots(figsize=(9, 7))
            fig.patch.set_facecolor(BG_COLOR)

            im = ax.imshow(corr.values, cmap="RdYlGn", aspect="auto", vmin=-1, vmax=1)

            ax.set_xticks(range(len(corr.columns)))
            ax.set_yticks(range(len(corr.columns)))
            labels = [c.replace("_", " ").title() for c in corr.columns]
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
            ax.set_yticklabels(labels, fontsize=9)

            # Annotate cells
            for i in range(len(corr)):
                for j in range(len(corr)):
                    val = corr.values[i, j]
                    color = "white" if abs(val) > 0.6 else "black"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=8, color=color, fontweight="bold")

            ax.set_title("Correlation Matrix", fontsize=14, fontweight="bold", pad=15)
            fig.colorbar(im, ax=ax, shrink=0.8)

            plt.tight_layout()

            filename = "correlation_heatmap.png"
            fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches="tight")
            plt.close(fig)

            return ChartConfig(
                chart_type="heatmap",
                title="Correlation Matrix",
                filename=filename,
                description="Heatmap showing correlations between all numeric variables",
            )
        except Exception:
            return None

    def _create_scatter(self, df, col_x, col_y, cat_col, output_dir) -> ChartConfig | None:
        """Scatter plot colored by category."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor(BG_COLOR)
            ax.set_facecolor(BG_COLOR)

            categories = df[cat_col].unique()
            for i, cat in enumerate(categories):
                mask = df[cat_col] == cat
                ax.scatter(df.loc[mask, col_x], df.loc[mask, col_y],
                           label=cat, color=COLORS[i % len(COLORS)], alpha=0.7, s=50)

            ax.set_title(f"{col_y.replace('_', ' ').title()} vs {col_x.replace('_', ' ').title()}",
                         fontsize=14, fontweight="bold", pad=15)
            ax.set_xlabel(col_x.replace("_", " ").title(), fontsize=11)
            ax.set_ylabel(col_y.replace("_", " ").title(), fontsize=11)
            ax.legend(title=cat_col.replace("_", " ").title(), fontsize=9)
            ax.grid(True, alpha=0.3, color=GRID_COLOR)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            plt.tight_layout()

            filename = f"{col_y}_vs_{col_x}_scatter.png"
            fig.savefig(os.path.join(output_dir, filename), dpi=150, bbox_inches="tight")
            plt.close(fig)

            return ChartConfig(
                chart_type="scatter",
                title=f"{col_y.replace('_', ' ').title()} vs {col_x.replace('_', ' ').title()}",
                filename=filename,
                description=f"Scatter plot of {col_y.replace('_', ' ')} against {col_x.replace('_', ' ')}, colored by {cat_col.replace('_', ' ')}",
            )
        except Exception:
            return None
