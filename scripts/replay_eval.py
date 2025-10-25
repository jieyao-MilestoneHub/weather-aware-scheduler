#!/usr/bin/env python
"""Replay evaluation dataset and report results."""

import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graph.builder import build_graph
from src.models.state import SchedulerState
from src.models.outputs import EventSummary, EventStatus


console = Console()


def load_dataset(dataset_path: str) -> list[dict[str, Any]]:
    """Load test cases from JSONL file.

    Args:
        dataset_path: Path to JSONL dataset file

    Returns:
        List of test case dictionaries
    """
    test_cases = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                test_cases.append(json.loads(line))
    return test_cases


def run_test_case(graph: Any, test_case: dict[str, Any]) -> dict[str, Any]:
    """Run a single test case through the graph.

    Args:
        graph: Compiled LangGraph
        test_case: Test case with input and expected results

    Returns:
        Result dictionary with status and details
    """
    try:
        # Initialize state
        initial_state = SchedulerState(input_text=test_case["input"])

        # Execute graph
        result_state = graph.invoke(initial_state)

        # Extract summary
        summary_dict = result_state.get("event_summary")
        if summary_dict:
            summary = EventSummary(**summary_dict)
            # status is already a string, not an enum
            actual_status = summary.status if isinstance(summary.status, str) else summary.status.value
        else:
            actual_status = "no_result"

        # Check if result matches expected
        expected_status = test_case.get("expected_status", "unknown")
        passed = actual_status == expected_status

        return {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "input": test_case["input"],
            "expected": expected_status,
            "actual": actual_status,
            "passed": passed,
            "summary": summary_dict.get("summary_text", "") if summary_dict else "",
            "reason": summary_dict.get("reason", "") if summary_dict else "",
        }

    except Exception as e:
        return {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "input": test_case["input"],
            "expected": test_case.get("expected_status", "unknown"),
            "actual": "error",
            "passed": False,
            "error": str(e),
        }


def print_results(results: list[dict[str, Any]]) -> None:
    """Print test results in a formatted table.

    Args:
        results: List of test result dictionaries
    """
    import os
    import sys

    # Check if we should use ASCII icons (Windows with non-UTF-8 encoding)
    use_ascii = False
    if os.environ.get("ASCII_ONLY", "").lower() in ("1", "true", "yes"):
        use_ascii = True
    elif sys.platform == "win32":
        try:
            encoding = sys.stdout.encoding or ""
            if "utf" not in encoding.lower():
                use_ascii = True
        except (AttributeError, TypeError):
            use_ascii = True

    # Create results table
    table = Table(title="Evaluation Results", show_header=True, header_style="bold magenta")
    table.add_column("Test ID", style="cyan", width=20)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Expected", justify="center", width=12)
    table.add_column("Actual", justify="center", width=12)
    table.add_column("Description", width=40)

    for result in results:
        status_icon = "[OK]" if result["passed"] else "[X]" if use_ascii else ("✓" if result["passed"] else "✗")
        status_color = "green" if result["passed"] else "red"

        table.add_row(
            result["test_id"],
            f"[{status_color}]{status_icon}[/{status_color}]",
            result["expected"],
            result["actual"],
            result["description"],
        )

    console.print(table)

    # Print summary statistics
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    success_rate = (passed / total * 100) if total > 0 else 0

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Total tests: {total}")
    console.print(f"  Passed: [green]{passed}[/green]")
    console.print(f"  Failed: [red]{total - passed}[/red]")
    console.print(f"  Success rate: [bold]{success_rate:.1f}%[/bold]")

    # Print failures details
    failures = [r for r in results if not r["passed"]]
    if failures:
        console.print("\n[bold red]Failures:[/bold red]")
        for failure in failures:
            console.print(f"\n  {failure['test_id']}: {failure['description']}")
            console.print(f"    Input: {failure['input']}")
            console.print(f"    Expected: {failure['expected']}")
            console.print(f"    Actual: {failure['actual']}")
            if "error" in failure:
                console.print(f"    Error: {failure['error']}")


def main() -> None:
    """Main entry point for dataset replay script."""
    import argparse

    parser = argparse.ArgumentParser(description="Replay evaluation dataset")
    parser.add_argument(
        "--dataset",
        default="datasets/eval_min5.jsonl",
        help="Path to JSONL dataset file (default: datasets/eval_min5.jsonl)",
    )
    parser.add_argument(
        "--ci-mode",
        action="store_true",
        help="Exit with error code if any tests fail (for CI/CD)",
    )
    args = parser.parse_args()

    console.print(f"[bold]Loading dataset:[/bold] {args.dataset}")

    # Load test cases
    try:
        test_cases = load_dataset(args.dataset)
        console.print(f"[dim]Loaded {len(test_cases)} test cases[/dim]\n")
    except FileNotFoundError:
        console.print(f"[red]Error: Dataset file not found: {args.dataset}[/red]")
        sys.exit(1)

    # Build graph
    console.print("[dim]Building scheduler graph...[/dim]")
    graph = build_graph()

    # Run test cases
    results = []
    with console.status("[bold green]Running tests...") as status:
        for i, test_case in enumerate(test_cases, 1):
            status.update(f"[bold green]Running test {i}/{len(test_cases)}: {test_case['id']}")
            result = run_test_case(graph, test_case)
            results.append(result)

    # Print results
    print_results(results)

    # Exit with appropriate code
    if args.ci_mode:
        passed_all = all(r["passed"] for r in results)
        sys.exit(0 if passed_all else 1)


if __name__ == "__main__":
    main()
