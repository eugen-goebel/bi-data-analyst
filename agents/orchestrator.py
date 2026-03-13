"""
Orchestrator — Coordinates the 5-phase BI analysis pipeline.

Manages the sequential flow:
DataLoader → PatternAgent → VisualizationAgent → InsightAgent → ReportGenerator
"""

import os
import tempfile
import anthropic

from agents.data_loader import DataLoaderAgent
from agents.pattern_agent import PatternAgent
from agents.visualization_agent import VisualizationAgent
from agents.insight_agent import InsightAgent, InsightResult
from utils.report_generator import generate_docx_report


class BIAnalysisOrchestrator:
    """
    Coordinates the five-phase pipeline for business data analysis.

    Phase 1: DataLoaderAgent reads and profiles the data file
    Phase 2: PatternAgent detects trends, correlations, outliers
    Phase 3: VisualizationAgent creates matplotlib charts
    Phase 4: InsightAgent generates AI-powered recommendations
    Phase 5: ReportGenerator builds DOCX with embedded charts
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-opus-4-6",
        output_dir: str = "output",
    ):
        self.model = model
        self.output_dir = output_dir
        self.client = anthropic.Anthropic(api_key=api_key)

        self._data_loader = DataLoaderAgent()
        self._pattern_agent = PatternAgent()
        self._viz_agent = VisualizationAgent()
        self._insight_agent = InsightAgent(self.client, model=model)

    def run(self, filepath: str) -> str:
        """
        Execute the full 5-phase pipeline.

        Args:
            filepath: Path to CSV or Excel file

        Returns:
            Absolute path to the generated DOCX report
        """
        # Phase 1: Load data
        print(f"\n[1/5] Loading and validating data file ...")
        summary, df = self._data_loader.load(filepath)
        print(f"      Loaded: {summary.row_count:,} rows, {summary.column_count} columns")
        print(f"      Date range: {summary.date_range or 'N/A'}")
        print(f"      Data quality: {summary.data_quality_score}/100")

        # Phase 2: Pattern detection
        print(f"\n[2/5] Detecting patterns — trends, correlations, outliers ...")
        patterns = self._pattern_agent.analyze(df, summary)
        print(f"      {patterns.summary}")

        # Phase 3: Visualization
        chart_dir = tempfile.mkdtemp(prefix="bi_charts_")
        print(f"\n[3/5] Generating charts ...")
        viz_result = self._viz_agent.create_charts(df, summary, patterns, chart_dir)
        print(f"      Created {len(viz_result.charts)} charts")

        # Phase 4: AI insights
        print(f"\n[4/5] Generating AI-powered insights and recommendations ...")
        insights = self._insight_agent.generate_insights(summary, patterns)
        print(f"      {len(insights.key_findings)} findings, "
              f"{len(insights.recommendations)} recommendations")

        # Phase 5: Report
        print(f"\n[5/5] Building DOCX report with embedded charts ...")
        report_path = generate_docx_report(
            summary=summary,
            patterns=patterns,
            viz_result=viz_result,
            insights=insights,
            output_dir=self.output_dir,
        )
        print(f"      Report saved: {report_path}")

        return report_path

    def run_with_mock(
        self, filepath: str, mock_insights: InsightResult
    ) -> str:
        """
        Run the pipeline with mock AI insights (for --dry-run).

        DataLoader, PatternAgent, and VisualizationAgent still run on
        real data. Only InsightAgent is replaced with mock data.
        """
        # Phase 1: Load data (real)
        print(f"\n[1/5] Loading and validating data file ...")
        summary, df = self._data_loader.load(filepath)
        print(f"      Loaded: {summary.row_count:,} rows, {summary.column_count} columns")
        print(f"      Date range: {summary.date_range or 'N/A'}")
        print(f"      Data quality: {summary.data_quality_score}/100")

        # Phase 2: Pattern detection (real)
        print(f"\n[2/5] Detecting patterns — trends, correlations, outliers ...")
        patterns = self._pattern_agent.analyze(df, summary)
        print(f"      {patterns.summary}")

        # Phase 3: Visualization (real)
        chart_dir = tempfile.mkdtemp(prefix="bi_charts_")
        print(f"\n[3/5] Generating charts ...")
        viz_result = self._viz_agent.create_charts(df, summary, patterns, chart_dir)
        print(f"      Created {len(viz_result.charts)} charts")

        # Phase 4: Mock insights
        print(f"\n[4/5] DRY RUN — using mock insights (skipping API call)")
        print(f"      {len(mock_insights.key_findings)} findings, "
              f"{len(mock_insights.recommendations)} recommendations")

        # Phase 5: Report
        print(f"\n[5/5] Building DOCX report with embedded charts ...")
        report_path = generate_docx_report(
            summary=summary,
            patterns=patterns,
            viz_result=viz_result,
            insights=mock_insights,
            output_dir=self.output_dir,
        )
        print(f"      Report saved: {report_path}")

        return report_path
