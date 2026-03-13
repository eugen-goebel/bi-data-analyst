"""
Tests for the VisualizationAgent.

Generates charts from sample data into a temporary directory and
validates the output files and metadata.
"""

import os
import pytest

from agents.data_loader import DataLoaderAgent
from agents.pattern_agent import PatternAgent
from agents.visualization_agent import (
    VisualizationAgent, VisualizationResult, ChartConfig,
)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SAMPLE_CSV = os.path.join(DATA_DIR, "sample_sales.csv")


@pytest.fixture(scope="module")
def viz_output(tmp_path_factory):
    """Generate charts once into a temp directory for the module."""
    loader = DataLoaderAgent()
    summary, df = loader.load(SAMPLE_CSV)
    pattern_agent = PatternAgent()
    patterns = pattern_agent.analyze(df, summary)

    output_dir = str(tmp_path_factory.mktemp("charts"))
    viz_agent = VisualizationAgent()
    result = viz_agent.create_charts(df, summary, patterns, output_dir)
    return result, output_dir


class TestVisualizationAgent:
    def test_returns_visualization_result(self, viz_output):
        result, _ = viz_output
        assert isinstance(result, VisualizationResult)

    def test_correct_number_of_charts(self, viz_output):
        result, _ = viz_output
        assert len(result.charts) == 5

    def test_chart_types_present(self, viz_output):
        result, _ = viz_output
        types = {c.chart_type for c in result.charts}
        assert "line" in types
        assert "bar" in types
        assert "pie" in types
        assert "heatmap" in types
        assert "scatter" in types

    def test_png_files_created(self, viz_output):
        result, output_dir = viz_output
        for chart in result.charts:
            path = os.path.join(output_dir, chart.filename)
            assert os.path.exists(path), f"Chart file not found: {chart.filename}"

    def test_files_non_empty(self, viz_output):
        result, output_dir = viz_output
        for chart in result.charts:
            path = os.path.join(output_dir, chart.filename)
            size = os.path.getsize(path)
            assert size > 0, f"Chart file is empty: {chart.filename}"

    def test_chart_dir_set(self, viz_output):
        result, output_dir = viz_output
        assert result.chart_dir == output_dir

    def test_all_charts_are_chart_config(self, viz_output):
        result, _ = viz_output
        for chart in result.charts:
            assert isinstance(chart, ChartConfig)
            assert chart.filename.endswith(".png")
            assert len(chart.title) > 0
            assert len(chart.description) > 0

    def test_filenames_unique(self, viz_output):
        result, _ = viz_output
        filenames = [c.filename for c in result.charts]
        assert len(filenames) == len(set(filenames)), "Chart filenames should be unique"
