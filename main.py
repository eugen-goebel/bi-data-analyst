"""
BI Data Analyst Agent — CLI entry point.

Analyzes business data files (CSV/Excel) using a multi-agent pipeline:
data loading, pattern detection, visualization, AI insights, and
professional DOCX report generation with embedded charts.
"""

import argparse
import os
import sys

from dotenv import load_dotenv


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generate AI-powered business intelligence reports from data files"
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        help="Path to a CSV or Excel file to analyze",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with sample data and mock insights (no API key needed)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory for reports (default: output/)",
    )
    parser.add_argument(
        "--model",
        default="claude-opus-4-6",
        help="Model to use for insight generation (default: claude-opus-4-6)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Export analysis results as CSV in addition to DOCX",
    )

    args = parser.parse_args()

    if args.dry_run:
        from agents.mock_data import MOCK_INSIGHTS
        from agents.orchestrator import BIAnalysisOrchestrator

        # Use sample data
        sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_sales.csv")

        print("=" * 60)
        print("  BI DATA ANALYST — DRY RUN")
        print(f"  Data: {os.path.basename(sample_path)}")
        print("=" * 60)

        orch = BIAnalysisOrchestrator(output_dir=args.output)
        report_path = orch.run_with_mock(sample_path, MOCK_INSIGHTS)

        if args.csv:
            from utils.csv_exporter import export_analysis_csv
            csv_path = orch.export_csv(MOCK_INSIGHTS)
            print(f"\n  CSV export: {csv_path}")

        print("\n" + "=" * 60)
        print(f"  Report ready: {report_path}")
        print("=" * 60)
    else:
        if not args.filepath:
            print("Error: Please provide a data file path or use --dry-run.")
            print("Usage: python main.py data.csv")
            print("       python main.py --dry-run")
            sys.exit(1)

        if not os.path.exists(args.filepath):
            print(f"Error: File not found: {args.filepath}")
            sys.exit(1)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set.")
            print("Set it via .env file or environment variable.")
            print("Or use --dry-run to test without an API key.")
            sys.exit(1)

        from agents.orchestrator import BIAnalysisOrchestrator

        print("=" * 60)
        print("  BI DATA ANALYST")
        print(f"  Data: {os.path.basename(args.filepath)}")
        print("=" * 60)

        orch = BIAnalysisOrchestrator(
            api_key=api_key,
            model=args.model,
            output_dir=args.output,
        )
        report_path = orch.run(args.filepath)

        if args.csv:
            csv_path = orch.export_csv()
            print(f"\n  CSV export: {csv_path}")

        print("\n" + "=" * 60)
        print(f"  Report ready: {report_path}")
        print("=" * 60)


if __name__ == "__main__":
    main()
