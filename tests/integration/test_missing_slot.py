"""
Integration tests for missing slot information and clarification flow.

Tests FR-005: System MUST ask for missing required fields exactly once before failing
Tests SC-003: Average clarification rounds ≤ 1
"""

import pytest
from freezegun import freeze_time
from datetime import datetime

from src.graph.builder import build_graph
from src.models.state import SchedulerState


@freeze_time("2025-10-17 10:00:00")
def test_missing_time_and_location_triggers_clarification():
    """
    Test that input missing time and location triggers clarification question.

    Input: "Meet Alice"
    Expected: System asks for missing time and location exactly once
    """
    graph = build_graph()

    # Initial request with missing time and location
    initial_state = SchedulerState(
        user_input="Meet Alice",
        clarification_needed=None,
        error=None
    )

    result = graph.invoke(initial_state)

    # Should detect missing fields and request clarification
    assert result.get("clarification_needed") is not None, "Should request clarification for missing fields"
    assert "time" in result.get("clarification_needed").lower() or "when" in result.get("clarification_needed").lower(), \
        "Should ask for time"
    assert "location" in result.get("clarification_needed").lower() or "where" in result.get("clarification_needed").lower(), \
        "Should ask for location"

    # Verify no event was created yet
    assert result.get("event_summary") is None, "Should not create event before clarification"


@freeze_time("2025-10-17 10:00:00")
def test_clarification_with_complete_info_creates_event():
    """
    Test that providing complete information after clarification creates event.

    Simulates user responding to clarification with: "2pm Taipei 60min"
    Expected: Event created successfully
    """
    graph = build_graph()

    # Simulate state after clarification was requested
    clarified_state = SchedulerState(
        user_input="2pm Taipei 60min",
        attendees=["Alice"],  # From original request
        description="Meet Alice",
        clarification_count=1,  # This is the first (and should be only) clarification
        clarification_needed=None,
        error=None
    )

    result = graph.invoke(clarified_state)

    # Should successfully create event
    assert result.get("event_summary") is not None, "Should create event after clarification"
    assert result.get("event_summary").get("status") in ["confirmed", "adjusted"], \
        "Event should be confirmed or adjusted based on weather/conflicts"
    assert result.get("clarification_count", 0) == 1, "Should have exactly 1 clarification round"


@freeze_time("2025-10-17 10:00:00")
def test_one_shot_clarification_strategy():
    """
    Test that system asks for clarification at most once per FR-005.

    If user provides incomplete info again, system should fail gracefully
    with clear error message including format examples.
    """
    graph = build_graph()

    # Simulate state after first clarification attempt that still has missing info
    second_attempt_state = SchedulerState(
        user_input="meet Bob",  # Still missing time and location
        clarification_count=1,  # Already asked once
        clarification_needed=None,
        error=None
    )

    result = graph.invoke(second_attempt_state)

    # Should fail gracefully after second attempt
    assert result.get("clarification_count", 0) == 1, "Should not exceed 1 clarification"
    assert result.get("error") is not None or result.get("clarification_needed") is not None, \
        "Should either error or request final clarification"

    # If error, it should include format examples
    if result.get("error"):
        assert any(example in result.get("error").lower() for example in ["2pm", "14:00", "taipei", "60min"]), \
            "Error message should include format examples"


@freeze_time("2025-10-17 10:00:00")
def test_missing_duration_uses_default():
    """
    Test that missing duration uses 60-minute default per assumptions in spec.md:182.

    Input: "Friday 2pm Taipei meet Alice"
    Expected: Event created with 60min default duration
    """
    graph = build_graph()

    initial_state = SchedulerState(
        user_input="Friday 2pm Taipei meet Alice",
        clarification_needed=None,
        error=None
    )

    result = graph.invoke(initial_state)

    # Should create event with default duration (no clarification needed)
    assert result.get("event_summary") is not None, "Should create event with default duration"
    assert result.get("duration_min") == 60, "Should use 60min default duration"
    assert result.get("clarification_count", 0) == 0, "Should not need clarification when only duration missing"


@freeze_time("2025-10-17 10:00:00")
def test_clarification_includes_format_examples():
    """
    Test that clarification messages include helpful format examples.

    Expected formats from T106 specification:
    - Time: e.g. 2pm, 14:00, afternoon
    - Location: e.g. Taipei, New York
    - Duration: e.g. 60min, 1 hour
    """
    graph = build_graph()

    initial_state = SchedulerState(
        user_input="Meeting with Charlie",  # Missing time, location, duration
        clarification_needed=None,
        error=None
    )

    result = graph.invoke(initial_state)

    clarification_message = result.get("clarification_needed") or ""

    # Should include examples for missing fields
    assert "e.g." in clarification_message or "example" in clarification_message.lower(), \
        "Should include format examples"

    # Check for time format examples
    if "time" in clarification_message.lower():
        assert any(ex in clarification_message for ex in ["2pm", "14:00", "afternoon"]), \
            "Should include time format examples"

    # Check for location examples
    if "location" in clarification_message.lower():
        assert any(ex in clarification_message for ex in ["Taipei", "New York", "city"]), \
            "Should include location format examples"
