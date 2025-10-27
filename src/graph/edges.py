"""Conditional edge routing logic for the scheduler graph."""
from src.models.state import SchedulerState
from src.models.outputs import ActionType


def conditional_edge_from_intent(state: SchedulerState) -> str:
    """
    Route from intent_and_slots node based on parsing success.
    
    Args:
        state: Current scheduler state
    
    Returns:
        Next node name: "check_weather" if valid, "error_recovery" if clarification needed
    """
    if state.get("error") or state.get("clarification_needed"):
        return "error_recovery"
    return "check_weather"


def conditional_edge_from_weather(state: SchedulerState) -> str:
    """
    Route from check_weather node based on weather check outcome.

    Args:
        state: Current scheduler state

    Returns:
        Next node name: "error_recovery" if service failed, "find_free_slot" if success/degraded
    """
    # If weather service failed, route to error_recovery for graceful degradation
    if state.get("error") and "weather" in state.get("error", "").lower():
        return "error_recovery"

    # Otherwise proceed to conflict check
    return "find_free_slot"


def conditional_edge_from_conflict(state: SchedulerState) -> str:
    """
    Route from find_free_slot node based on conflict detection outcome.

    Args:
        state: Current scheduler state

    Returns:
        Next node name: "error_recovery" if service failed, "confirm_or_adjust" otherwise
    """
    # If calendar service failed, route to error_recovery for graceful degradation
    if state.get("error") and "calendar" in state.get("error", "").lower():
        return "error_recovery"

    # Otherwise go to confirm_or_adjust for policy decision
    return "confirm_or_adjust"


def conditional_edge_from_policy(state: SchedulerState) -> str:
    """
    Route from confirm_or_adjust node based on policy decision.
    
    Args:
        state: Current scheduler state
    
    Returns:
        Next node name: "create_event" to finalize or return alternatives
    """
    # Always go to create_event to generate final output
    return "create_event"


def conditional_edge_from_error(state: SchedulerState) -> str:
    """
    Route from error_recovery node based on recovery outcome.

    Implements T082: Conditional routing after error recovery with:
    - Loop back to intent_and_slots if clarification answered (retry_count == 1)
    - Proceed to create_event if degraded (service failures cleared)
    - End if fatal error (event_summary already created)

    Args:
        state: Current scheduler state

    Returns:
        Next node name: "intent_and_slots" (retry), "create_event" (degrade/end)
    """
    retry_count = state.get("retry_count", 0)

    # If event_summary already created (fatal error), end
    if state.get("event_summary"):
        return "create_event"  # Will pass through (summary already set)

    # If error was cleared (graceful degradation with degradation_notes), continue to next step
    if not state.get("error") and state.get("degradation_notes"):
        # Service failures degraded, continue workflow to check other services
        # Check if we've already attempted calendar check (no_conflicts key exists)
        if "no_conflicts" not in state:
            # Haven't checked calendar yet (weather failed first), continue to find_free_slot
            return "find_free_slot"
        else:
            # Already checked calendar (or both failed), proceed to create_event
            return "create_event"

    # If error was cleared but no degradation (successfully parsed after retry)
    if not state.get("error") and not state.get("clarification_needed"):
        # Route back to check_weather to continue normal flow
        if state.get("city") and state.get("dt"):
            return "check_weather"  # Continue from where we left off
        else:
            return "create_event"  # Can't continue, create error summary

    # If clarification needed, END the graph and return to user (FR-005)
    # User will provide additional info in a new request with clarification_count preserved
    if state.get("clarification_needed"):
        return "create_event"  # END node (will skip event creation if clarification_needed)

    # Otherwise (max retries or unrecoverable), end
    return "create_event"
