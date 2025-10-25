"""Graph visualization export utilities."""

import os
from pathlib import Path
from typing import Any


def export_to_mermaid(graph: Any) -> str:
    """Export LangGraph to Mermaid format.

    Uses LangGraph's built-in draw_mermaid() method to generate
    a flowchart representation of the state machine.

    Args:
        graph: Compiled LangGraph instance

    Returns:
        Mermaid diagram string

    Example:
        >>> graph = build_graph()
        >>> mermaid_str = export_to_mermaid(graph)
        >>> print(mermaid_str)
        %%{init: {'flowchart': {'curve': 'linear'}}}%%
        graph TD
        ...
    """
    try:
        # Use LangGraph's built-in visualization
        return graph.get_graph().draw_mermaid()
    except AttributeError:
        # Fallback if method not available
        return _generate_fallback_mermaid()


def _generate_fallback_mermaid() -> str:
    """Generate a fallback Mermaid diagram if LangGraph method unavailable.

    Returns:
        Basic Mermaid flowchart string
    """
    return """%%{init: {'flowchart': {'curve': 'linear'}}}%%
graph TD
    Start([START]) --> A[intent_and_slots]
    A -->|Valid slot| B[check_weather]
    A -->|Missing info| F[error_recovery]
    B -->|Weather checked| C[find_free_slot]
    C -->|Availability checked| D[confirm_or_adjust]
    D -->|CREATE| E[create_event]
    D -->|ADJUST_TIME| E
    D -->|ADJUST_PLACE| E
    D -->|PROPOSE_CANDIDATES| E
    E --> End([END])
    F -->|Retry| A
    F -->|Max retries| E

    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#ffe1f5
    style D fill:#f5ffe1
    style E fill:#e1ffe1
    style F fill:#ffe1e1
"""


def export_to_graphviz(graph: Any) -> str:
    """Export LangGraph to Graphviz DOT format.

    Generates a DOT format representation suitable for rendering
    with Graphviz tools.

    Args:
        graph: Compiled LangGraph instance

    Returns:
        DOT format string

    Example:
        >>> graph = build_graph()
        >>> dot_str = export_to_graphviz(graph)
        >>> # Save and render: dot -Tsvg flow.dot -o flow.svg
    """
    try:
        # Try LangGraph's built-in method if available
        return graph.get_graph().draw_ascii()
    except AttributeError:
        # Generate custom DOT format
        return _generate_dot_format()


def _generate_dot_format() -> str:
    """Generate DOT format visualization.

    Returns:
        Graphviz DOT format string
    """
    return """digraph SchedulerWorkflow {
    rankdir=TD;
    node [shape=rectangle, style=rounded];

    // Nodes
    start [shape=circle, label="START"];
    intent_and_slots [label="Intent & Slots\\n(Parse Input)", fillcolor="#e1f5ff", style="filled,rounded"];
    check_weather [label="Check Weather\\n(Get Forecast)", fillcolor="#fff4e1", style="filled,rounded"];
    find_free_slot [label="Find Free Slot\\n(Check Calendar)", fillcolor="#ffe1f5", style="filled,rounded"];
    confirm_or_adjust [label="Confirm or Adjust\\n(Policy Decision)", fillcolor="#f5ffe1", style="filled,rounded", shape=diamond];
    create_event [label="Create Event\\n(Finalize)", fillcolor="#e1ffe1", style="filled,rounded"];
    error_recovery [label="Error Recovery\\n(Retry)", fillcolor="#ffe1e1", style="filled,rounded"];
    end [shape=doublecircle, label="END"];

    // Edges
    start -> intent_and_slots;
    intent_and_slots -> check_weather [label="Valid slot"];
    intent_and_slots -> error_recovery [label="Parse error"];
    check_weather -> find_free_slot [label="Weather checked"];
    find_free_slot -> confirm_or_adjust [label="Checked"];
    confirm_or_adjust -> create_event [label="CREATE"];
    confirm_or_adjust -> create_event [label="ADJUST"];
    confirm_or_adjust -> create_event [label="PROPOSE"];
    create_event -> end;
    error_recovery -> intent_and_slots [label="Retry"];
    error_recovery -> create_event [label="Give up"];
}
"""


def save_visualization(graph: Any, output_dir: str = "graph") -> dict[str, str]:
    """Save graph visualization to both Mermaid and ASCII formats.

    Creates output directory if it doesn't exist and saves
    visualization files.

    Args:
        graph: Compiled LangGraph instance
        output_dir: Directory to save files (default: "graph")

    Returns:
        Dictionary with paths to created files:
        {
            "mermaid": "graph/flow.mermaid",
            "dot": "graph/flow.dot"
        }

    Example:
        >>> graph = build_graph()
        >>> paths = save_visualization(graph)
        >>> print(f"Saved to: {paths['mermaid']}")
    """
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Export to Mermaid
    mermaid_str = export_to_mermaid(graph)
    mermaid_path = os.path.join(output_dir, "flow.mermaid")
    with open(mermaid_path, "w", encoding="utf-8") as f:
        f.write(mermaid_str)

    result = {"mermaid": mermaid_path}

    # Export to DOT (optional - requires grandalf)
    try:
        dot_str = export_to_graphviz(graph)
        dot_path = os.path.join(output_dir, "flow.dot")
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot_str)
        result["dot"] = dot_path
    except ImportError:
        # grandalf not installed - skip DOT generation
        pass
    except Exception:
        # Other errors - skip DOT generation
        pass

    return result
