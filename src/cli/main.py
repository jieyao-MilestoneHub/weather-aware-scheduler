"""Main CLI application using Typer."""
import typer
from rich.console import Console
from rich import print as rprint
from src.graph.builder import build_graph
from src.graph.visualizer import save_visualization
from src.models.state import SchedulerState
from src.services.formatter import format_event_summary
from src.models.outputs import EventSummary
from src.cli import prompts

app = typer.Typer(
    name="weather-scheduler",
    help="Weather-Aware Scheduler - Schedule meetings with natural language",
    add_completion=False
)
console = Console()


@app.command()
def schedule(
    input: str = typer.Argument(..., help="Natural language scheduling request"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format (machine-readable)")
):
    """
    Schedule a meeting using natural language input.

    Examples:
        weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"
        weather-scheduler schedule "tomorrow afternoon coffee with Bob"
        weather-scheduler schedule "Monday 10am review" --json
    """
    import time
    import json as json_lib

    try:
        start_time = time.time()

        # Build the graph with progress indicator (T096)
        if not json_output:
            with console.status("[bold green]Building scheduler graph...") as status:
                graph = build_graph()
                if verbose:
                    elapsed = time.time() - start_time
                    console.print(f"[dim]Graph built in {elapsed:.2f}s[/dim]")
        else:
            graph = build_graph()

        # Initialize state
        initial_state = SchedulerState(input_text=input)

        # Execute graph with progress indicator (T096)
        if not json_output and not verbose:
            with console.status(f"[bold green]Processing: {input[:50]}..."):
                result_state = graph.invoke(initial_state)
        else:
            if verbose and not json_output:
                console.print(f"[dim]Processing: {input}[/dim]")
            result_state = graph.invoke(initial_state)

        # Calculate total time
        total_time = time.time() - start_time

        # Format and display output
        if result_state.get("event_summary"):
            summary_dict = result_state["event_summary"]
            summary = EventSummary(**summary_dict)

            # JSON output mode (T097)
            if json_output:
                output_data = {
                    "status": "success",
                    "execution_time_seconds": round(total_time, 3),
                    "result": summary_dict
                }
                print(json_lib.dumps(output_data, indent=2, default=str))
            else:
                # Rich formatted output
                formatted_output = format_event_summary(summary)
                rprint(formatted_output)

                if verbose:
                    console.print(f"\n[dim]Completed in {total_time:.2f}s[/dim]")
        else:
            if json_output:
                output_data = {
                    "status": "error",
                    "execution_time_seconds": round(total_time, 3),
                    "error": result_state.get("error", "No result generated")
                }
                print(json_lib.dumps(output_data, indent=2))
            else:
                console.print("[red]✗ No result generated[/red]")
                if result_state.get("error"):
                    console.print(f"[yellow]Error: {result_state['error']}[/yellow]")

    except Exception as e:
        if json_output:
            error_data = {
                "status": "fatal_error",
                "error": str(e),
                "error_type": type(e).__name__
            }
            print(json_lib.dumps(error_data, indent=2))
            raise typer.Exit(code=1)
        else:
            console.print(f"[red]✗ Error: {str(e)}[/red]")
            if verbose:
                console.print_exception()
            raise typer.Exit(code=1)


@app.command()
def visualize(
    output_dir: str = typer.Option("graph", "--output", "-o", help="Output directory for visualization files")
):
    """
    Generate and save workflow visualization diagrams.

    Creates Mermaid and DOT format diagrams showing the decision flow.

    Examples:
        weather-scheduler visualize
        weather-scheduler visualize --output docs/diagrams
    """
    import os
    import sys

    # Use ASCII icons on Windows with non-UTF-8 encoding
    use_ascii = os.environ.get("ASCII_ONLY", "").lower() in ("1", "true", "yes")
    if not use_ascii and sys.platform == "win32":
        try:
            encoding = sys.stdout.encoding or ""
            use_ascii = "utf" not in encoding.lower()
        except (AttributeError, TypeError):
            use_ascii = True

    success_icon = "[OK]" if use_ascii else "✓"
    error_icon = "[X]" if use_ascii else "✗"

    try:
        console.print("[dim]Building scheduler graph...[/dim]")
        graph = build_graph()

        console.print(f"[dim]Generating visualizations in {output_dir}/...[/dim]")
        paths = save_visualization(graph, output_dir)

        console.print(f"[green]{success_icon} Visualizations created successfully![/green]")
        console.print(f"  * Mermaid: {paths['mermaid']}")
        if 'dot' in paths:
            console.print(f"  * DOT: {paths['dot']}")
            console.print("\n[dim]To render DOT file:[/dim]")
            console.print(f"  dot -Tsvg {paths['dot']} -o {output_dir}/flow.svg")
        else:
            console.print(f"\n[yellow]Note: DOT visualization skipped (install 'grandalf' for full support)[/yellow]")

    except Exception as e:
        console.print(f"[red]{error_icon} Error generating visualizations: {str(e)}[/red]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Weather-Aware Scheduler[/bold]")
    console.print("Version: 0.1.0")
    console.print("Python CLI for weather-aware meeting scheduling")


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
