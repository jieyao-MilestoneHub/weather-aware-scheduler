"""Event summary formatting with Rich console output."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from src.models.outputs import EventSummary


console = Console()


def format_event_summary(summary: EventSummary) -> str:
    """
    Format EventSummary as Rich-formatted string for CLI output.
    
    Includes:
    - Status icons: ✓ (confirmed), ⚠ (adjusted), ✗ (error)
    - Color coding
    - Structured layout with reason and notes
    
    Args:
        summary: EventSummary object to format
    
    Returns:
        Rich-formatted string for display
    
    Examples:
        >>> summary = EventSummary(status="confirmed", summary_text="Meeting", 
        ...                        reason="No conflicts", notes="Clear weather")
        >>> output = format_event_summary(summary)
        >>> "✓" in output
        True
    """
    # Determine icon and color based on status
    if summary.status == "confirmed":
        icon = "✓"
        color = "green"
        title = "Event Created"
    elif summary.status == "adjusted":
        icon = "⚠"
        color = "yellow"
        title = "Schedule Adjusted"
    elif summary.status == "conflict":
        icon = "⚠"
        color = "yellow"
        title = "Time Conflict Detected"
    else:  # error
        icon = "✗"
        color = "red"
        title = "Unable to Schedule"
    
    # Build output text
    lines = []
    lines.append(f"[bold {color}]{icon} {title}[/bold {color}]\n")
    lines.append(f"[bold]Summary:[/bold]")
    lines.append(f"  {summary.summary_text}\n")
    lines.append(f"[bold]Reason:[/bold]")
    lines.append(f"  {summary.reason}\n")
    
    if summary.notes:
        lines.append(f"[bold]Notes:[/bold]")
        lines.append(f"  {summary.notes}")
    
    if summary.alternatives:
        lines.append(f"\n[bold]Alternative Times:[/bold]")
        for i, alt in enumerate(summary.alternatives, 1):
            lines.append(f"  {i}. {alt}")
    
    return "\n".join(lines)


def format_conflict_alternatives(alternatives: list[str]) -> str:
    """
    Format conflict alternatives as Rich table.
    
    Args:
        alternatives: List of alternative time slot strings
    
    Returns:
        Rich-formatted table string
    """
    table = Table(title="Available Time Slots", show_header=True)
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Time", style="white")
    table.add_column("Duration Available", style="green")
    
    for i, alt in enumerate(alternatives, 1):
        # Parse alternative string (format: "Friday at 15:30 (60 min available)")
        parts = alt.split(" (")
        time_str = parts[0] if parts else alt
        duration_str = parts[1].rstrip(")") if len(parts) > 1 else "N/A"
        
        table.add_row(str(i), time_str, duration_str)
    
    return table
