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
    Route from check_weather node (always continue to conflict check).
    
    Args:
        state: Current scheduler state
    
    Returns:
        Next node name: "find_free_slot" (graceful degradation if weather fails)
    """
    # Always proceed to conflict check, even if weather check failed
    return "find_free_slot"


def conditional_edge_from_conflict(state: SchedulerState) -> str:
    """
    Route from find_free_slot node based on conflict detection.
    
    Args:
        state: Current scheduler state
    
    Returns:
        Next node name: "confirm_or_adjust" to make policy decision
    """
    # Always go to confirm_or_adjust for policy decision
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

    # If error was cleared (graceful degradation), proceed with what we have
    if not state.get("error") and not state.get("clarification_needed"):
        # Services degraded but we can continue
        # Route back to check_weather to continue normal flow
        if state.get("city") and state.get("dt"):
            return "check_weather"  # Continue from where we left off
        else:
            return "create_event"  # Can't continue, create error summary

    # If clarification needed and first retry, loop back to parse
    if state.get("clarification_needed") and retry_count < 2:
        return "intent_and_slots"

    # Otherwise (max retries or unrecoverable), end
    return "create_event"
