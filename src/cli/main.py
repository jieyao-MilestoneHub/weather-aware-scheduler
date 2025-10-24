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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """
    Schedule a meeting using natural language input.
    
    Examples:
        weather-scheduler schedule "Friday 2pm Taipei meet Alice 60min"
        weather-scheduler schedule "tomorrow afternoon coffee with Bob"
    """
    try:
        # Build the graph
        if verbose:
            console.print("[dim]Building scheduler graph...[/dim]")
        
        graph = build_graph()
        
        # Initialize state
        initial_state = SchedulerState(input_text=input)
        
        if verbose:
            console.print(f"[dim]Processing: {input}[/dim]")
        
        # Execute graph
        result_state = graph.invoke(initial_state)
        
        # Format and display output
        if result_state.get("event_summary"):
            summary_dict = result_state["event_summary"]
            summary = EventSummary(**summary_dict)
            formatted_output = format_event_summary(summary)
            rprint(formatted_output)
        else:
            console.print("[red]✗ No result generated[/red]")
            if result_state.get("error"):
                console.print(f"[yellow]Error: {result_state['error']}[/yellow]")
    
    except Exception as e:
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
    try:
        console.print("[dim]Building scheduler graph...[/dim]")
        graph = build_graph()

        console.print(f"[dim]Generating visualizations in {output_dir}/...[/dim]")
        paths = save_visualization(graph, output_dir)

        console.print("[green]✓ Visualizations created successfully![/green]")
        console.print(f"  • Mermaid: {paths['mermaid']}")
        console.print(f"  • DOT: {paths['dot']}")
        console.print("\n[dim]To render DOT file:[/dim]")
        console.print(f"  dot -Tsvg {paths['dot']} -o {output_dir}/flow.svg")

    except Exception as e:
        console.print(f"[red]✗ Error generating visualizations: {str(e)}[/red]")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Weather-Aware Scheduler[/bold]")
    console.print("Version: 0.1.0")
    console.print("Python CLI for weather-aware meeting scheduling")


if __name__ == "__main__":
    app()
