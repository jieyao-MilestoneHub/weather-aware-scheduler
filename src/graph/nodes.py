"""LangGraph node implementations for the scheduler workflow."""

from datetime import datetime as dt_type, timedelta
from typing import Any

from src.models.entities import RiskCategory, Slot, WeatherCondition
from src.models.outputs import ActionType, EventStatus, EventSummary, PolicyDecision
from src.models.state import SchedulerState
from src.services.parser import parse_natural_language, ParseError
from src.services.validator import validate_slot, ValidationError
from src.tools.base import CalendarTool, WeatherTool, CalendarServiceError, WeatherServiceError
from src.lib.config import load_config
from src.lib.retry import retry


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


# Retry-wrapped tool calls for resilience (FR-019, FR-020)
@retry(max_attempts=2, retry_delay=0.5, exceptions=(WeatherServiceError,))
def _get_forecast_with_retry(city: str, dt: dt_type) -> WeatherCondition | None:
    """Get weather forecast with automatic retry on failure."""
    if _weather_tool is None:
        return None
    return _weather_tool.get_forecast(city, dt)


@retry(max_attempts=2, retry_delay=0.5, exceptions=(CalendarServiceError,))
def _check_availability_with_retry(dt: dt_type, duration_min: int) -> dict | None:
    """Check calendar availability with automatic retry on failure."""
    if _calendar_tool is None:
        return None
    return _calendar_tool.check_slot_availability(dt, duration_min)


def intent_and_slots_node(state: SchedulerState) -> SchedulerState:
    """Parse user input and extract slot information.

    Args:
        state: Current state with user_input or input_text

    Returns:
        Updated state with parsed city, dt, duration_min, attendees
    """
    try:
        # Parse natural language input (support both input_text and user_input for compatibility)
        user_text = state.get("input_text") or state.get("user_input", "")
        slot = parse_natural_language(user_text)

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
    # Skip if we have parsing errors
    if state.get("error"):
        return state

    # Use retry-wrapped function (returns None on failure after retries)
    weather = _get_forecast_with_retry(state["city"], state["dt"])

    if weather is None:
        # Graceful degradation: Continue without weather info
        state["error"] = "Weather service error after retries"
        # Error recovery node will handle degradation
    else:
        state["weather"] = {
            "prob_rain": weather.prob_rain,
            "risk_category": weather.risk_category.value,
            "description": weather.description
        }
        state["rain_risk"] = weather.risk_category.value

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
    # Skip if we have previous errors
    if state.get("error"):
        return state

    # Use retry-wrapped function (returns None on failure after retries)
    result = _check_availability_with_retry(state["dt"], state["duration_min"])

    if result is None:
        # Graceful degradation: Continue without conflict check
        state["error"] = "Calendar service error after retries"
        # Error recovery node will handle degradation
        return state

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
        # Check weather at this slot (with retry)
        weather = _get_forecast_with_retry("", current)  # City not needed for mock
        has_good_weather = weather and weather.risk_category != RiskCategory.HIGH

        # Check calendar availability (with retry)
        result = _check_availability_with_retry(current, duration_min)
        has_no_conflicts = result and result["status"] == "available"

        # If both conditions met, return this slot
        if has_good_weather and has_no_conflicts:
            return current

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

    # If clarification needed, skip event creation and return state to user (FR-005)
    if state.get("clarification_needed"):
        return state

    # Check if we have errors that should stop event creation
    # Note: Service failures with degradation_notes should continue, not stop
    if state.get("error") and not state.get("degradation_notes"):
        # Only stop for non-recoverable errors (parsing failures, etc.)
        state["event_summary"] = EventSummary(
            status=EventStatus.ERROR,
            summary_text="Failed to schedule event",
            reason=state["error"],
            notes="Please resolve the error and try again"
        ).model_dump()
        return state

    # Clear error if we have degradation notes (service failures that can be worked around)
    if state.get("degradation_notes"):
        state["error"] = None

    policy_decision = state.get("policy_decision", {})
    action = policy_decision.get("action")

    # If no policy decision but we have degradation notes, create event anyway (degraded mode)
    if not action and state.get("degradation_notes"):
        action = ActionType.CREATE.value
        policy_decision = {
            "action": ActionType.CREATE.value,
            "reason": "Event created with service degradation",
            "notes": None,
            "adjustments": {}
        }

    # Only create if action is CREATE
    if action == ActionType.CREATE.value:
        try:
            # Prepare notes including any degradation warnings
            notes_parts = []
            if policy_decision.get("notes"):
                notes_parts.append(policy_decision["notes"])

            # Add degradation notes if services failed
            if state.get("degradation_notes"):
                notes_parts.extend(state["degradation_notes"])

            combined_notes = "\n".join(notes_parts) if notes_parts else None

            event = _calendar_tool.create_event(
                city=state["city"],
                dt=state["dt"],
                duration_min=state["duration_min"],
                attendees=state["attendees"],
                notes=combined_notes
            )

            state["event_summary"] = EventSummary(
                status=EventStatus.CONFIRMED,
                summary_text=f"Meeting scheduled in {state['city']}",
                reason=policy_decision["reason"],
                event_id=event.event_id,
                notes=combined_notes or event.notes
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
    """Handle errors with one-shot clarification and graceful degradation.

    Implements T081: Comprehensive error recovery with:
    - One-shot clarification for missing/ambiguous input (FR-005)
    - Graceful degradation for service failures
    - Format examples on second failure
    - Maximum 1 clarification attempt per FR-005

    Args:
        state: Current state with error or clarification_needed

    Returns:
        Updated state with clarification prompt, degradation notes, or error summary
    """
    state["retry_count"] = state.get("retry_count", 0) + 1

    # Case 1: Clarification needed (missing required fields)
    if state.get("clarification_needed") or (state.get("error") and not ("service" in state.get("error", "").lower())):
        # Initialize clarification_count if not present
        clarification_count = state.get("clarification_count", 0)

        if clarification_count == 0:
            # First clarification: Generate precise follow-up question with examples
            error_msg = state.get("error", "")

            # Build specific clarification based on what's missing
            clarification_parts = []

            if "time" in error_msg.lower() or "datetime" in error_msg.lower():
                clarification_parts.append("• Time: (e.g., '2pm', '14:00', 'afternoon')")

            if "location" in error_msg.lower() or "city" in error_msg.lower():
                clarification_parts.append("• Location: (e.g., 'Taipei', 'New York')")

            if "duration" in error_msg.lower():
                clarification_parts.append("• Duration: (e.g., '60min', '1 hour', default: 60 minutes)")

            # If no specific fields identified, ask for all
            if not clarification_parts:
                clarification_parts = [
                    "• Time: (e.g., '2pm', '14:00', 'afternoon')",
                    "• Location: (e.g., 'Taipei', 'New York')",
                    "• Duration: (optional, default: 60 minutes)"
                ]

            clarification_text = "Please provide missing information:\n" + "\n".join(clarification_parts)
            state["clarification_needed"] = clarification_text
            state["clarification_count"] = 1  # Increment to 1
            state["error"] = None  # Clear error after setting clarification

        elif clarification_count >= 1:
            # Second failure: Provide complete format example and give up (FR-005: max 1 clarification)
            error_message = (
                "Required information missing after clarification attempt. "
                "Please provide a complete request with: "
                "Date (e.g. Friday, tomorrow, 2025-10-17), "
                "Time (e.g. 2pm, 14:00, afternoon), "
                "Location (e.g. Taipei, New York), "
                "Duration (e.g. 60min, 1 hour - optional), "
                "Attendees (e.g. meet Alice, with Bob - optional). "
                "Example: 'Friday 2pm Taipei meet Alice 60min'"
            )
            state["event_summary"] = EventSummary(
                status=EventStatus.ERROR,
                summary_text="Unable to parse scheduling request",
                reason="Required information missing after clarification attempt",
                notes=error_message
            ).model_dump()
            state["clarification_needed"] = None
            state["error"] = error_message

    # Case 2: Service failures (weather/calendar unavailable)
    elif state.get("error") and ("service" in state["error"].lower() or "error" in state["error"].lower()):
        # Check which service failed
        error_msg = state["error"]

        if "weather" in error_msg.lower():
            # Weather service failed - degrade gracefully
            state["error"] = None  # Clear error
            state["weather"] = None  # Mark as unavailable

            # Add degradation note with context to be picked up by create_event
            city = state.get("city", "your location")
            dt = state.get("dt")
            time_context = f" at {dt.strftime('%A %I:%M %p')}" if dt else ""

            if not state.get("degradation_notes"):
                state["degradation_notes"] = []
            state["degradation_notes"].append(
                f"⚠️ Weather service unavailable - manual weather check recommended for {city}{time_context}"
            )

        elif "calendar" in error_msg.lower():
            # Calendar service failed - degrade gracefully
            state["error"] = None  # Clear error
            state["no_conflicts"] = True  # Assume no conflicts

            if not state.get("degradation_notes"):
                state["degradation_notes"] = []
            state["degradation_notes"].append(
                "⚠️ Calendar service unavailable - manual conflict check recommended"
            )

        else:
            # Generic service error
            if not state.get("degradation_notes"):
                state["degradation_notes"] = []
            state["degradation_notes"].append(
                f"⚠️ Service error: {error_msg} - proceeding with available information"
            )
            state["error"] = None  # Clear error to allow continuation

    # Case 3: Maximum retries exceeded
    elif state["retry_count"] >= 2:
        state["event_summary"] = EventSummary(
            status=EventStatus.ERROR,
            summary_text="Failed to schedule event after multiple attempts",
            reason=state.get("error", "Unknown error"),
            notes="Maximum retry attempts exceeded. Please check your input and try again."
        ).model_dump()
        state["error"] = None  # Clear error

    # Case 4: Other errors - generic handling
    else:
        # Try to continue with what we have
        if state.get("error") and state["retry_count"] < 2:
            state["clarification_needed"] = (
                f"An error occurred: {state['error']}\n"
                "Please try rephrasing your request or provide more details."
            )

    return state
