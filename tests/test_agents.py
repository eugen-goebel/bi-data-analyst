"""
Tests for InsightAgent (mocked Anthropic client) and BIAnalysisOrchestrator.

Mocks the Anthropic API to avoid real API calls.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from agents.insight_agent import InsightAgent, InsightResult, KeyFinding, Recommendation
from agents.data_loader import DataLoaderAgent, DataSummary, ColumnProfile
from agents.pattern_agent import PatternAgent, PatternAnalysis
from agents.mock_data import MOCK_INSIGHTS

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
SAMPLE_CSV = os.path.join(DATA_DIR, "sample_sales.csv")


def _make_mock_client(mock_insight_result: InsightResult):
    """Create a mock Anthropic client that returns the given InsightResult."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.parsed_output = mock_insight_result
    client.messages.parse.return_value = mock_response
    return client


@pytest.fixture
def mock_client():
    return _make_mock_client(MOCK_INSIGHTS)


@pytest.fixture
def sample_data():
    loader = DataLoaderAgent()
    summary, df = loader.load(SAMPLE_CSV)
    agent = PatternAgent()
    patterns = agent.analyze(df, summary)
    return summary, patterns


# ---------------------------------------------------------------------------
# InsightAgent tests
# ---------------------------------------------------------------------------

class TestInsightAgent:
    def test_returns_insight_result(self, mock_client, sample_data):
        summary, patterns = sample_data
        agent = InsightAgent(client=mock_client, model="claude-opus-4-6")
        result = agent.generate_insights(summary, patterns)
        assert isinstance(result, InsightResult)

    def test_passes_correct_model(self, mock_client, sample_data):
        summary, patterns = sample_data
        agent = InsightAgent(client=mock_client, model="claude-opus-4-6")
        agent.generate_insights(summary, patterns)
        call_kwargs = mock_client.messages.parse.call_args
        assert call_kwargs.kwargs["model"] == "claude-opus-4-6"

    def test_uses_structured_output(self, mock_client, sample_data):
        summary, patterns = sample_data
        agent = InsightAgent(client=mock_client)
        agent.generate_insights(summary, patterns)
        call_kwargs = mock_client.messages.parse.call_args
        assert call_kwargs.kwargs["output_format"] == InsightResult

    def test_passes_system_prompt(self, mock_client, sample_data):
        summary, patterns = sample_data
        agent = InsightAgent(client=mock_client)
        agent.generate_insights(summary, patterns)
        call_kwargs = mock_client.messages.parse.call_args
        assert "system" in call_kwargs.kwargs
        assert len(call_kwargs.kwargs["system"]) > 0

    def test_mock_insights_valid(self):
        """Verify the MOCK_INSIGHTS object is a valid InsightResult."""
        assert isinstance(MOCK_INSIGHTS, InsightResult)
        assert len(MOCK_INSIGHTS.key_findings) >= 5
        assert len(MOCK_INSIGHTS.recommendations) >= 5
        assert len(MOCK_INSIGHTS.risk_alerts) >= 4
        assert len(MOCK_INSIGHTS.opportunities) >= 4


# ---------------------------------------------------------------------------
# Orchestrator tests
# ---------------------------------------------------------------------------

class TestOrchestrator:
    @patch("agents.orchestrator.anthropic.Anthropic")
    def test_orchestrator_initializes(self, mock_anthropic_class):
        from agents.orchestrator import BIAnalysisOrchestrator
        orch = BIAnalysisOrchestrator(api_key="fake-key")
        assert orch is not None
        assert orch.model == "claude-opus-4-6"

    @patch("agents.orchestrator.anthropic.Anthropic")
    def test_run_with_mock_produces_docx(self, mock_anthropic_class, tmp_path):
        from agents.orchestrator import BIAnalysisOrchestrator
        output_dir = str(tmp_path / "output")
        orch = BIAnalysisOrchestrator(api_key="fake-key", output_dir=output_dir)
        report_path = orch.run_with_mock(SAMPLE_CSV, MOCK_INSIGHTS)
        assert report_path.endswith(".docx")
        assert os.path.exists(report_path)
        assert os.path.getsize(report_path) > 0

    @patch("agents.orchestrator.anthropic.Anthropic")
    def test_run_with_mock_creates_output_dir(self, mock_anthropic_class, tmp_path):
        from agents.orchestrator import BIAnalysisOrchestrator
        output_dir = str(tmp_path / "new_output_dir")
        assert not os.path.exists(output_dir)
        orch = BIAnalysisOrchestrator(api_key="fake-key", output_dir=output_dir)
        orch.run_with_mock(SAMPLE_CSV, MOCK_INSIGHTS)
        assert os.path.isdir(output_dir)
