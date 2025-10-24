"""LangGraph node implementations for the scheduler workflow."""

from datetime import datetime as dt_type, timedelta
from typing import Any

from src.models.entities import RiskCategory, Slot
from src.models.outputs import ActionType, EventStatus, EventSummary, PolicyDecision
from src.models.state import SchedulerState
from src.services.parser import parse_natural_language, ParseError
from src.services.validator import validate_slot, ValidationError
from src.tools.base import CalendarTool, WeatherTool, CalendarServiceError, WeatherServiceError
from src.lib.config import load_config


# Global tool instances (will be configured via dependency injection)
_weather_tool: WeatherTool | None = None
_calendar_tool: CalendarTool | None = None


def configure_tools(weather_tool: WeatherTool, calendar_tool: CalendarTool):
    """Configure tool instances for nodes.

    Args:
        weather_tool: Weather forecast tool (mock or real)
        calendar_tool: Calendar operations tool (mock or real)
    """
    global _weather_tool, _calendar_tool
    _weather_tool = weather_tool
    _calendar_tool = calendar_tool


def intent_and_slots_node(state: SchedulerState) -> SchedulerState:
    """Parse user input and extract slot information.

    Args:
        state: Current state with user_input

    Returns:
        Updated state with parsed city, dt, duration_min, attendees
    """
    try:
        # Parse natural language input
        slot = parse_natural_language(state["input_text"])

        # Validate the parsed slot
        validate_slot(slot)

        # Update state with parsed data
        state["city"] = slot.city
        state["dt"] = slot.datetime
        state["duration_min"] = slot.duration
        state["attendees"] = slot.attendees
        state["description"] = slot.description

        # Clear any previous errors
        state["error"] = None
        state["clarification_needed"] = None

    except (ParseError, ValidationError) as e:
        state["error"] = str(e)
        state["clarification_needed"] = "Please provide more details about the scheduling request"

    return state


def check_weather_node(state: SchedulerState) -> SchedulerState:
    """Check weather forecast for the requested time and location.

    Args:
        state: Current state with city and dt

    Returns:
        Updated state with weather info and rain_risk
    """
    if not _weather_tool:
        state["error"] = "Weather tool not configured"
        return state

    # Skip if we have parsing errors
    if state.get("error"):
        return state

    try:
        weather = _weather_tool.get_forecast(state["city"], state["dt"])

        state["weather"] = {
            "prob_rain": weather.prob_rain,
            "risk_category": weather.risk_category.value,
            "description": weather.description
        }
        state["rain_risk"] = weather.risk_category.value

    except WeatherServiceError as e:
        state["error"] = f"Weather service error: {str(e)}"

    return state


def find_free_slot_node(state: SchedulerState) -> SchedulerState:
    """Check calendar for conflicts and find alternative if needed.

    If rain risk is HIGH or calendar conflict exists, searches for
    an alternative slot with good weather and no conflicts.

    Args:
        state: Current state with dt, duration_min, and weather info

    Returns:
        Updated state with conflict info and suggested_time if needed
    """
    if not _calendar_tool:
        state["error"] = "Calendar tool not configured"
        return state

    if not _weather_tool:
        state["error"] = "Weather tool not configured"
        return state

    # Skip if we have previous errors
    if state.get("error"):
        return state

    try:
        # Check if requested slot has conflicts
        result = _calendar_tool.check_slot_availability(state["dt"], state["duration_min"])

        if result["status"] == "conflict":
            state["no_conflicts"] = False
            state["conflicts"] = [result["conflict_details"]]
            state["proposed"] = result.get("candidates", [])
        else:
            state["no_conflicts"] = True
            state["conflicts"] = []

        # Check if we need to find alternative due to weather or conflicts
        rain_risk = state.get("rain_risk", "low")
        needs_alternative = (
            rain_risk == RiskCategory.HIGH.value or
            not state.get("no_conflicts", True)
        )

        if needs_alternative:
            # Search for alternative slot with good weather and no conflicts
            suggested = _find_weather_aware_slot(
                state["dt"],
                state["duration_min"],
                search_hours=8
            )
            if suggested:
                state["suggested_time"] = suggested

    except (CalendarServiceError, WeatherServiceError) as e:
        state["error"] = f"Service error: {str(e)}"

    return state


def _find_weather_aware_slot(
    start_dt: dt_type,
    duration_min: int,
    search_hours: int = 8
) -> dt_type | None:
    """Find next slot with good weather and no calendar conflicts.

    Args:
        start_dt: Starting datetime to search from
        duration_min: Required duration in minutes
        search_hours: How many hours to search ahead

    Returns:
        Suggested datetime, or None if none found
    """
    # Search in 30-minute increments
    current = start_dt
    end_search = start_dt + timedelta(hours=search_hours)

    while current < end_search:
        # Check weather at this slot
        try:
            weather = _weather_tool.get_forecast("", current)  # City not needed for mock
            has_good_weather = weather.risk_category != RiskCategory.HIGH

            # Check calendar availability
            result = _calendar_tool.check_slot_availability(current, duration_min)
            has_no_conflicts = result["status"] == "available"

            # If both conditions met, return this slot
            if has_good_weather and has_no_conflicts:
                return current

        except (WeatherServiceError, CalendarServiceError):
            pass  # Skip this slot if service errors

        # Move to next 30-minute slot
        current += timedelta(minutes=30)

    return None


def confirm_or_adjust_node(state: SchedulerState) -> SchedulerState:
    """Make policy decision: create, adjust time, adjust place, or propose alternatives.

    Args:
        state: Current state with weather and conflict info

    Returns:
        Updated state with policy_decision
    """
    # Skip if we have previous errors
    if state.get("error"):
        return state

    # Decision logic
    has_conflicts = not state.get("no_conflicts", True)
    rain_risk = state.get("rain_risk", "low")

    # Case 1: Conflicts detected → propose alternatives
    if has_conflicts:
        decision = PolicyDecision(
            action=ActionType.PROPOSE_CANDIDATES,
            reason="Calendar conflict detected at requested time",
            notes="Please select from alternative time slots",
            adjustments={"candidates": state.get("proposed", [])}
        )

    # Case 2: High rain risk → adjust time
    elif rain_risk == RiskCategory.HIGH.value:
        decision = PolicyDecision(
            action=ActionType.ADJUST_TIME,
            reason="High rain probability detected at requested time",
            notes="Consider rescheduling to avoid weather risk",
            adjustments={"weather_warning": state["weather"]["description"]}
        )

    # Case 3: Moderate rain risk and outdoor → suggest indoor
    elif rain_risk == RiskCategory.MODERATE.value:
        decision = PolicyDecision(
            action=ActionType.ADJUST_PLACE,
            reason="Moderate rain probability detected",
            notes="Consider indoor venue or bring umbrella",
            adjustments={"indoor_suggestion": True}
        )

    # Case 4: All clear → create event
    else:
        decision = PolicyDecision(
            action=ActionType.CREATE,
            reason="No conflicts detected, weather conditions acceptable",
            notes=None,
            adjustments={}
        )

    state["policy_decision"] = decision.model_dump()

    return state


def create_event_node(state: SchedulerState) -> SchedulerState:
    """Create calendar event if policy decision is CREATE.

    Args:
        state: Current state with policy_decision

    Returns:
        Updated state with event_summary
    """
    if not _calendar_tool:
        state["error"] = "Calendar tool not configured"
        return state

    # Skip if we have previous errors
    if state.get("error"):
        # Create error summary
        state["event_summary"] = EventSummary(
            status=EventStatus.ERROR,
            summary_text="Failed to schedule event",
            reason=state["error"],
            notes="Please resolve the error and try again"
        ).model_dump()
        return state

    policy_decision = state.get("policy_decision", {})
    action = policy_decision.get("action")

    # Only create if action is CREATE
    if action == ActionType.CREATE.value:
        try:
            event = _calendar_tool.create_event(
                city=state["city"],
                dt=state["dt"],
                duration_min=state["duration_min"],
                attendees=state["attendees"],
                notes=policy_decision.get("notes")
            )

            state["event_summary"] = EventSummary(
                status=EventStatus.CONFIRMED,
                summary_text=f"Meeting scheduled in {state['city']}",
                reason=policy_decision["reason"],
                event_id=event.event_id,
                notes=event.notes
            ).model_dump()

        except CalendarServiceError as e:
            state["event_summary"] = EventSummary(
                status=EventStatus.ERROR,
                summary_text="Failed to create event",
                reason=str(e),
                notes="Calendar service error"
            ).model_dump()

    # If action is PROPOSE_CANDIDATES
    elif action == ActionType.PROPOSE_CANDIDATES.value:
        state["event_summary"] = EventSummary(
            status=EventStatus.CONFLICT,
            summary_text="Calendar conflict detected",
            reason=policy_decision["reason"],
            alternatives=state.get("proposed", []),
            notes=policy_decision.get("notes")
        ).model_dump()

    # If action is ADJUST_TIME or ADJUST_PLACE
    elif action in [ActionType.ADJUST_TIME.value, ActionType.ADJUST_PLACE.value]:
        state["event_summary"] = EventSummary(
            status=EventStatus.ADJUSTED,
            summary_text="Event requires adjustment",
            reason=policy_decision["reason"],
            notes=policy_decision.get("notes"),
            suggested_time=state.get("suggested_time")
        ).model_dump()

    return state


def error_recovery_node(state: SchedulerState) -> SchedulerState:
    """Handle errors and increment retry count.

    Args:
        state: Current state with error

    Returns:
        Updated state with incremented retry_count
    """
    state["retry_count"] = state.get("retry_count", 0) + 1

    # If too many retries, give up
    if state["retry_count"] >= 3:
        state["event_summary"] = EventSummary(
            status=EventStatus.ERROR,
            summary_text="Failed to schedule event after multiple attempts",
            reason=state.get("error", "Unknown error"),
            notes="Maximum retry attempts exceeded"
        ).model_dump()

    return state
