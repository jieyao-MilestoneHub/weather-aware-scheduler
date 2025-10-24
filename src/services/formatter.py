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


def format_conflict_alternatives(alternatives: list, duration_min: int = 60) -> Table:
    """
    Format conflict alternatives as Rich table.

    Args:
        alternatives: List of alternative datetimes or strings
        duration_min: Duration in minutes for the meeting

    Returns:
        Rich Table object for display
    """
    from datetime import datetime

    table = Table(title="Available Time Slots", show_header=True, header_style="bold magenta")
    table.add_column("Option", style="cyan bold", width=8, justify="center")
    table.add_column("Time", style="white")
    table.add_column("Duration Available", style="green")

    for i, alt in enumerate(alternatives[:3], 1):  # Limit to 3 options
        if isinstance(alt, datetime):
            # Format datetime as friendly string
            time_str = alt.strftime("%A at %I:%M %p")  # e.g., "Friday at 03:30 PM"
            duration_str = f"{duration_min} min available"
        elif isinstance(alt, str):
            # Already formatted string
            parts = alt.split(" (")
            time_str = parts[0] if parts else alt
            duration_str = parts[1].rstrip(")") if len(parts) > 1 else "N/A"
        else:
            # Fallback
            time_str = str(alt)
            duration_str = "N/A"

        table.add_row(str(i), time_str, duration_str)

    return table
