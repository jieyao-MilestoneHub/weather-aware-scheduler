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
    Route from error_recovery node based on retry count and error type.
    
    Args:
        state: Current scheduler state
    
    Returns:
        Next node name: retry, degrade, or end
    """
    retry_count = state.get("retry_count", 0)
    
    # If too many retries, give up
    if retry_count >= 3:
        return "create_event"  # Will create error summary
    
    # If clarification was provided, retry parsing
    if state.get("clarification_needed"):
        return "intent_and_slots"
    
    # Otherwise, proceed with degraded service
    return "create_event"
