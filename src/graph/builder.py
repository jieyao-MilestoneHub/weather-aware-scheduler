"""Build and compile the LangGraph state machine."""

import os
from typing import Any

from langgraph.graph import StateGraph, END

from src.models.state import SchedulerState
from src.graph.nodes import (
    intent_and_slots_node,
    check_weather_node,
    find_free_slot_node,
    confirm_or_adjust_node,
    create_event_node,
    error_recovery_node,
    configure_tools,
)
from src.graph.edges import (
    conditional_edge_from_intent,
    conditional_edge_from_weather,
    conditional_edge_from_conflict,
    conditional_edge_from_policy,
    conditional_edge_from_error,
)
from src.tools.mock_weather import MockWeatherTool
from src.tools.mock_calendar import MockCalendarTool


def build_graph() -> Any:
    """Build and compile the LangGraph state machine.

    Creates a StateGraph with 6 nodes and conditional routing edges.

    Environment Variables:
        MOCK_MODE: Set to "false" or "False" to use real APIs (requires OPENAI_API_KEY)
                   Set to "true" or "True" to use mock tools (default)

    Graph structure:
        START → intent_and_slots → check_weather → find_free_slot
          ↓ (if clarification needed)
        error_recovery → (loop back to intent_and_slots)
          ↓ (continue if valid)
        find_free_slot → confirm_or_adjust → create_event → END
          ↓ (if conflict or weather risk)
        confirm_or_adjust (suggests alternatives)

    Returns:
        Compiled LangGraph that can be invoked with initial state

    Examples:
        >>> graph = build_graph()
        >>> result = graph.invoke({
        ...     "user_input": "Friday 2pm Taipei meet Alice 60min",
        ...     "attendees": [],
        ...     "conflicts": [],
        ...     "proposed": [],
        ...     "retry_count": 0
        ... })
    """
    # Check MOCK_MODE environment variable (default: true)
    mock_mode = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

    if mock_mode:
        # Use mock tools for testing (no API keys required)
        weather_tool = MockWeatherTool()
        calendar_tool = MockCalendarTool()
    else:
        # Use real tools with OpenAI API (requires OPENAI_API_KEY)
        from src.tools.real_weather import RealWeatherTool
        from src.tools.real_calendar import RealCalendarTool

        weather_tool = RealWeatherTool()
        calendar_tool = RealCalendarTool()

    configure_tools(weather_tool, calendar_tool)

    # Create StateGraph with SchedulerState
    workflow = StateGraph(SchedulerState)

    # Add 6 nodes with actual implementations
    workflow.add_node("intent_and_slots", intent_and_slots_node)
    workflow.add_node("check_weather", check_weather_node)
    workflow.add_node("find_free_slot", find_free_slot_node)
    workflow.add_node("confirm_or_adjust", confirm_or_adjust_node)
    workflow.add_node("create_event", create_event_node)
    workflow.add_node("error_recovery", error_recovery_node)

    # Set entry point
    workflow.set_entry_point("intent_and_slots")

    # Add conditional edges (Phase 3 implementation)
    # Sunny path: intent → weather → conflict → adjust → create
    workflow.add_conditional_edges(
        "intent_and_slots",
        conditional_edge_from_intent,
        {
            "check_weather": "check_weather",
            "error_recovery": "error_recovery"
        }
    )

    workflow.add_conditional_edges(
        "check_weather",
        conditional_edge_from_weather,
        {
            "find_free_slot": "find_free_slot",
            "error_recovery": "error_recovery"
        }
    )

    workflow.add_conditional_edges(
        "find_free_slot",
        conditional_edge_from_conflict,
        {
            "confirm_or_adjust": "confirm_or_adjust",
            "error_recovery": "error_recovery"
        }
    )

    workflow.add_conditional_edges(
        "confirm_or_adjust",
        conditional_edge_from_policy,
        {"create_event": "create_event"}
    )

    workflow.add_edge("create_event", END)

    # Error recovery edge with conditional routing (T083)
    # Can route to: intent_and_slots (retry parse), check_weather (degraded continue), find_free_slot (after weather fail), create_event (end)
    workflow.add_conditional_edges(
        "error_recovery",
        conditional_edge_from_error,
        {
            "intent_and_slots": "intent_and_slots",
            "check_weather": "check_weather",
            "find_free_slot": "find_free_slot",
            "create_event": "create_event"
        }
    )

    # Compile and return
    return workflow.compile()


def export_graph_visualization(graph: Any, output_path: str = "graph/flow.mermaid") -> str:
    """Export graph visualization to Mermaid format.

    Args:
        graph: Compiled LangGraph
        output_path: Path to save Mermaid diagram (default: graph/flow.mermaid)

    Returns:
        Mermaid diagram as string

    Note:
        This is a placeholder implementation. Full visualization will be implemented
        in Phase 6 (User Story 4).
    """
    # Placeholder - will be implemented in US4 (T068-T070)
    mermaid_str = """
    graph TD
        START --> intent_and_slots
        intent_and_slots --> check_weather
        check_weather --> find_free_slot
        find_free_slot --> confirm_or_adjust
        confirm_or_adjust --> create_event
        create_event --> END
        intent_and_slots -.-> error_recovery
        error_recovery -.-> intent_and_slots
    """
    return mermaid_str.strip()
