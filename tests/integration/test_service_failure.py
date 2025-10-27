"""
Integration tests for service failure and graceful degradation.

Tests FR-019: System MUST retry once when weather service fails
Tests FR-020: System MUST retry once when calendar service fails
Tests FR-021: System MUST gracefully degrade with clear message when service unavailable
Tests SC-010: 100% of service failures result in clear user guidance
"""

import pytest
from freezegun import freeze_time
from unittest.mock import patch, MagicMock

from src.graph.builder import build_graph
from src.models.state import SchedulerState
from src.tools.base import WeatherServiceError, CalendarServiceError


@freeze_time("2025-10-17 10:00:00")
def test_weather_service_failure_retries_once_then_degrades():
    """
    Test that weather service failure triggers retry, then graceful degradation.

    Expected behavior per FR-019:
    1. First call fails → retry
    2. Second call fails → proceed without weather check
    3. Event created with warning note
    """
    graph = build_graph()

    # Patch the weather tool to raise error
    with patch('src.tools.mock_weather.MockWeatherTool.get_forecast') as mock_forecast:
        mock_forecast.side_effect = WeatherServiceError("Weather service temporarily unavailable")

        initial_state = SchedulerState(
            user_input="Friday 2pm Taipei meet Alice 60min",
            clarification_needed=None,
            error=None
        )

        result = graph.invoke(initial_state)

        # Should retry once (2 calls total)
        assert mock_forecast.call_count == 2, f"Should retry once (expected 2 calls, got {mock_forecast.call_count})"

        # Should create event despite weather failure
        assert result.get("event_summary") is not None, "Should create event even when weather unavailable"

        # Should include manual check recommendation
        event_summary = result.get("event_summary", {})
        notes_lower = (event_summary.get("notes") or "").lower()
        assert "manual" in notes_lower and "weather" in notes_lower, \
            "Should recommend manual weather check in notes"
        assert "weather" in notes_lower and ("unavailable" in notes_lower or "check" in notes_lower), \
            "Should explain weather service was unavailable"


@freeze_time("2025-10-17 10:00:00")
def test_calendar_service_failure_retries_once_then_degrades():
    """
    Test that calendar service failure triggers retry, then graceful degradation.

    Expected behavior per FR-020:
    1. First call fails → retry
    2. Second call fails → proceed without conflict check
    3. Event created with warning note
    """
    graph = build_graph()

    # Patch the calendar tool to raise error
    with patch('src.tools.mock_calendar.MockCalendarTool.check_slot_availability') as mock_slot:
        mock_slot.side_effect = CalendarServiceError("Calendar service temporarily unavailable")

        initial_state = SchedulerState(
            user_input="Friday 2pm Taipei meet Alice 60min",
            clarification_needed=None,
            error=None
        )

        result = graph.invoke(initial_state)

        # Should retry once (2 calls total)
        assert mock_slot.call_count == 2, f"Should retry once (expected 2 calls, got {mock_slot.call_count})"

        # Should create event despite calendar failure
        assert result.get("event_summary") is not None, "Should create event even when calendar unavailable"

        # Should include manual conflict check recommendation
        event_summary = result.get("event_summary", {})
        notes_lower = (event_summary.get("notes") or "").lower()
        assert "manual" in notes_lower and "conflict" in notes_lower, \
            "Should recommend manual conflict check in notes"


@freeze_time("2025-10-17 10:00:00")
def test_weather_service_succeeds_on_retry():
    """
    Test that transient weather service failures succeed on retry.

    Expected: First call fails, second call succeeds → normal weather processing
    """
    graph = build_graph()

    call_count = 0

    def mock_forecast_with_retry(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise WeatherServiceError("Temporary network error")
        # Second call succeeds
        from src.models.entities import WeatherCondition
        return WeatherCondition(
            prob_rain=20,
            risk_category="low",
            description="Clear skies"
        )

    with patch('src.tools.mock_weather.MockWeatherTool.get_forecast', side_effect=mock_forecast_with_retry):
        initial_state = SchedulerState(
            user_input="Friday 2pm Taipei meet Alice 60min",
            clarification_needed=None,
            error=None
        )

        result = graph.invoke(initial_state)

        # Should have retried and succeeded
        assert call_count == 2, "Should have called forecast twice (fail then succeed)"
        assert result.get("event_summary") is not None, "Should create event after successful retry"
        assert result.get("weather") is not None, "Should have weather data after successful retry"

        # Should NOT have degradation warning since retry succeeded
        event_summary = result.get("event_summary", {})
        notes_lower = (event_summary.get("notes") or "").lower()
        assert "unavailable" not in notes_lower, "Should not mention service unavailable after successful retry"


@freeze_time("2025-10-17 10:00:00")
def test_both_services_fail_creates_event_with_warnings():
    """
    Test that both weather and calendar service failures result in event creation
    with both warning notes.

    Expected: Event created with dual warnings about manual checks needed
    """
    graph = build_graph()

    with patch('src.tools.mock_weather.MockWeatherTool.get_forecast') as mock_weather, \
         patch('src.tools.mock_calendar.MockCalendarTool.check_slot_availability') as mock_calendar:

        mock_weather.side_effect = WeatherServiceError("Weather service down")
        mock_calendar.side_effect = CalendarServiceError("Calendar service down")

        initial_state = SchedulerState(
            user_input="Friday 2pm Taipei meet Alice 60min",
            clarification_needed=None,
            error=None
        )

        result = graph.invoke(initial_state)

        # Should still create event
        assert result.get("event_summary") is not None, "Should create event despite both service failures"

        # Should mention both manual checks needed
        event_summary = result.get("event_summary", {})
        notes_lower = (event_summary.get("notes") or "").lower()
        assert "weather" in notes_lower, "Should mention weather check needed"
        assert "conflict" in notes_lower or "calendar" in notes_lower, \
            "Should mention conflict/calendar check needed"
        assert "manual" in notes_lower, "Should recommend manual checks"


@freeze_time("2025-10-17 10:00:00")
def test_service_failure_notes_are_actionable():
    """
    Test that service failure notes provide clear, actionable guidance per SC-010.

    Expected format per T113:
    "Weather data unavailable. Event created without weather check.
     Please manually verify weather conditions for [city] at [time]"
    """
    graph = build_graph()

    with patch('src.tools.mock_weather.MockWeatherTool.get_forecast') as mock_forecast:
        mock_forecast.side_effect = WeatherServiceError("Service unavailable")

        initial_state = SchedulerState(
            user_input="Friday 2pm Taipei meet Alice 60min",
            clarification_needed=None,
            error=None
        )

        result = graph.invoke(initial_state)

        event_summary = result.get("event_summary", {})
        notes = event_summary.get("notes") or ""

        # Should include what happened
        assert "unavailable" in notes.lower() or "failed" in notes.lower(), \
            "Should explain service was unavailable"

        # Should include what user should do
        assert "manual" in notes.lower() or "verify" in notes.lower() or "check" in notes.lower(), \
            "Should tell user to manually verify"

        # Should include relevant context (city and/or time)
        assert "Taipei" in notes or "Friday" in notes or "city" in notes.lower(), \
            "Should include relevant context (location or time)"
