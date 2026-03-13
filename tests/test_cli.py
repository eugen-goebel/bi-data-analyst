"""
Tests for the CLI entry point (main.py).

Uses subprocess to invoke main.py as a separate process.
"""

import os
import sys
import subprocess

import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(PROJECT_DIR, "main.py")


def _run_cli(*args, env_override=None):
    """Run main.py with the given arguments and return the CompletedProcess."""
    env = os.environ.copy()
    # Remove API key so it doesn't interfere unless we explicitly set it
    env.pop("ANTHROPIC_API_KEY", None)
    if env_override:
        env.update(env_override)
    return subprocess.run(
        [sys.executable, MAIN_PY, *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
        env=env,
        timeout=120,
    )


class TestCLI:
    def test_dry_run_succeeds(self, tmp_path):
        result = _run_cli("--dry-run", "--output", str(tmp_path))
        assert result.returncode == 0

    def test_dry_run_creates_docx(self, tmp_path):
        _run_cli("--dry-run", "--output", str(tmp_path))
        docx_files = [f for f in os.listdir(tmp_path) if f.endswith(".docx")]
        assert len(docx_files) == 1, f"Expected 1 DOCX file, found: {docx_files}"

    def test_dry_run_mentions_all_steps(self, tmp_path):
        result = _run_cli("--dry-run", "--output", str(tmp_path))
        output = result.stdout
        assert "[1/5]" in output
        assert "[2/5]" in output
        assert "[3/5]" in output
        assert "[4/5]" in output
        assert "[5/5]" in output

    def test_no_filepath_no_dry_run_fails(self):
        result = _run_cli()
        assert result.returncode != 0
        assert "Error" in result.stdout or "error" in result.stdout.lower()

    def test_missing_api_key_fails(self, tmp_path):
        """Running with a filepath but no API key should fail."""
        # Create a dummy CSV so the file-exists check passes
        dummy = tmp_path / "dummy.csv"
        dummy.write_text("a,b\n1,2\n3,4\n")
        result = _run_cli(str(dummy), env_override={"ANTHROPIC_API_KEY": ""})
        assert result.returncode != 0
        assert "ANTHROPIC_API_KEY" in result.stdout

    def test_dry_run_output_contains_report_path(self, tmp_path):
        result = _run_cli("--dry-run", "--output", str(tmp_path))
        assert "Report ready" in result.stdout or "report" in result.stdout.lower()
