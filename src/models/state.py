"""LangGraph state model for the scheduler."""

from datetime import datetime as dt_type
from typing import Any, TypedDict


class SchedulerState(TypedDict, total=False):
    """State model for the LangGraph scheduler.

    This state is passed between nodes in the graph and accumulates
    information as the scheduling request is processed.
    """

    # Extracted slot information
    city: str | None
    dt: dt_type | None
    duration_min: int | None
    attendees: list[str]
    description: str | None

    # Weather information
    weather: dict[str, Any] | None
    rain_risk: str | None  # "high" | "moderate" | "low"

    # Conflict information
    conflicts: list[dict[str, Any]]
    proposed: list[dt_type]
    no_conflicts: bool

    # Error handling
    error: str | None
    clarification_needed: str | None
    retry_count: int

    # Final output
    event_summary: dict[str, Any] | None
    policy_decision: dict[str, Any] | None

    # Original input
    input_text: str
    user_input: str  # Alias for backward compatibility
