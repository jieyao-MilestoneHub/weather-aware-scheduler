"""
Contract tests for CalendarTool interface.

These tests ensure that all CalendarTool implementations (Mock, MCP, etc.) adhere to the same contract:
- find_free_slot() returns dict with required keys {status, conflict_details, next_available, candidates}
- create_event() returns CalendarEvent with event_id
- Exception handling: Raise CalendarServiceError (not generic Exception)

This allows seamless switching between implementations via feature flags.
"""

import pytest
from datetime import datetime, timezone

from src.tools.base import CalendarTool, CalendarServiceError
from src.tools.mock_calendar import MockCalendarTool
from src.models.entities import CalendarEvent


class TestCalendarToolContract:
    """Contract tests that all CalendarTool implementations must pass."""

    @pytest.fixture
    def calendar_tool(self) -> CalendarTool:
        """
        Return the CalendarTool implementation to test.

        Currently tests MockCalendarTool. When MCP implementation is added,
        parameterize this fixture to test both implementations.
        """
        return MockCalendarTool()

    def test_find_free_slot_returns_dict(self, calendar_tool):
        """
        Test that find_free_slot returns a dict, not CalendarEvent or other type.

        Contract requirement: Return value must be dict with slot availability info.
        """
        dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)
        duration_min = 60

        result = calendar_tool.find_free_slot(dt, duration_min)

        assert isinstance(result, dict), \
            f"Expected dict, got {type(result).__name__}"

    def test_find_free_slot_has_required_keys(self, calendar_tool):
        """
        Test that find_free_slot dict has all required keys.

        Required keys per contract:
        - status: "available" or "conflict"
        - conflict_details: dict (may be empty if status is "available")
        - next_available: datetime (next free slot)
        - candidates: list[datetime] (top 3 alternative slots)
        """
        dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)
        duration_min = 60

        result = calendar_tool.find_free_slot(dt, duration_min)

        # Check required keys
        assert "status" in result, "Result must have 'status' key"
        assert "conflict_details" in result, "Result must have 'conflict_details' key"
        assert "next_available" in result, "Result must have 'next_available' key"
        assert "candidates" in result, "Result must have 'candidates' key"

        # Verify key types
        assert result["status"] in ["available", "conflict"], \
            f"status must be 'available' or 'conflict', got {result['status']}"

        assert isinstance(result["conflict_details"], dict), \
            f"conflict_details must be dict, got {type(result['conflict_details'])}"

        if result["next_available"] is not None:
            assert isinstance(result["next_available"], datetime), \
                f"next_available must be datetime, got {type(result['next_available'])}"

        assert isinstance(result["candidates"], list), \
            f"candidates must be list, got {type(result['candidates'])}"

    def test_find_free_slot_candidates_list_length(self, calendar_tool):
        """
        Test that candidates list contains up to 3 alternative time slots.

        Contract requirement per FR-012: Propose next 3 available time slots.
        """
        dt = datetime(2025, 10, 17, 15, 0, tzinfo=timezone.utc)  # Known conflict time
        duration_min = 30

        result = calendar_tool.find_free_slot(dt, duration_min)

        candidates = result["candidates"]

        # Should have candidates (up to 3)
        assert len(candidates) <= 3, f"Should have at most 3 candidates, got {len(candidates)}"

        if result["status"] == "conflict":
            assert len(candidates) > 0, "Should provide alternative candidates when conflict detected"

        # Each candidate should be a datetime
        for idx, candidate in enumerate(candidates):
            assert isinstance(candidate, datetime), \
                f"Candidate {idx} must be datetime, got {type(candidate)}"

    def test_create_event_returns_calendar_event(self, calendar_tool):
        """
        Test that create_event returns a CalendarEvent instance.

        Contract requirement: Return value must be CalendarEvent with event_id.
        """
        city = "Taipei"
        dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)
        duration_min = 60
        attendees = ["Alice"]
        notes = "Test event"

        result = calendar_tool.create_event(
            city=city,
            dt=dt,
            duration_min=duration_min,
            attendees=attendees,
            notes=notes
        )

        assert isinstance(result, CalendarEvent), \
            f"Expected CalendarEvent, got {type(result).__name__}"

    def test_calendar_event_has_event_id(self, calendar_tool):
        """
        Test that CalendarEvent has non-empty event_id.

        Contract requirement: event_id must be present for event tracking.
        """
        city = "New York"
        dt = datetime(2025, 10, 20, 10, 0, tzinfo=timezone.utc)
        duration_min = 90
        attendees = ["Bob", "Charlie"]

        result = calendar_tool.create_event(
            city=city,
            dt=dt,
            duration_min=duration_min,
            attendees=attendees,
            notes=None
        )

        assert hasattr(result, 'event_id'), "CalendarEvent must have event_id field"
        assert result.event_id is not None, "event_id must not be None"
        assert len(str(result.event_id)) > 0, "event_id must be non-empty"

    def test_calendar_event_has_required_fields(self, calendar_tool):
        """
        Test that CalendarEvent contains all required fields per spec.md:148.

        Required fields:
        - event_id
        - attendees (list)
        - city
        - datetime
        - duration
        - reason
        - notes
        - status
        """
        city = "London"
        dt = datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc)
        duration_min = 45
        attendees = ["Alice", "David"]
        notes = "Team meeting"

        result = calendar_tool.create_event(
            city=city,
            dt=dt,
            duration_min=duration_min,
            attendees=attendees,
            notes=notes
        )

        # Verify all required fields exist
        required_fields = ['event_id', 'attendees', 'city', 'datetime', 'duration', 'reason', 'notes', 'status']
        for field in required_fields:
            assert hasattr(result, field), f"CalendarEvent must have '{field}' field"

        # Verify field types
        assert isinstance(result.attendees, list), "attendees must be list"
        assert isinstance(result.city, str), "city must be string"
        assert isinstance(result.datetime, datetime), "datetime must be datetime"
        assert isinstance(result.duration, int), "duration must be int"

    def test_raises_calendar_service_error_on_failure(self, calendar_tool):
        """
        Test that service failures raise CalendarServiceError, not generic Exception.

        Contract requirement: Must raise specific CalendarServiceError for proper error handling.
        """
        # If tool supports error simulation (like MockCalendarTool with raise_on_error parameter)
        if isinstance(calendar_tool, MockCalendarTool):
            tool_with_error = MockCalendarTool(raise_on_error=True)
            dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)
            duration_min = 60

            with pytest.raises(CalendarServiceError) as exc_info:
                tool_with_error.find_free_slot(dt, duration_min)

            # Should raise CalendarServiceError specifically
            assert isinstance(exc_info.value, CalendarServiceError), \
                "Must raise CalendarServiceError, not generic Exception"

            # Should have descriptive error message
            assert len(str(exc_info.value)) > 0, "Error message should not be empty"

    def test_create_event_raises_error_on_failure(self, calendar_tool):
        """
        Test that create_event also raises CalendarServiceError on failure.

        Contract requirement: Consistent error handling across all methods.
        """
        if isinstance(calendar_tool, MockCalendarTool):
            tool_with_error = MockCalendarTool(raise_on_error=True)

            with pytest.raises(CalendarServiceError):
                tool_with_error.create_event(
                    city="Taipei",
                    dt=datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc),
                    duration_min=60,
                    attendees=["Alice"],
                    notes="Test"
                )

    def test_find_free_slot_accepts_correct_parameters(self, calendar_tool):
        """
        Test that find_free_slot accepts required parameter types.

        Signature: find_free_slot(dt: datetime, duration_min: int) -> dict
        """
        dt = datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc)
        duration_min = 60

        # Should not raise TypeError
        result = calendar_tool.find_free_slot(dt, duration_min)

        assert isinstance(result, dict), "Should return dict"

    def test_create_event_accepts_correct_parameters(self, calendar_tool):
        """
        Test that create_event accepts required parameter types.

        Signature: create_event(city: str, dt: datetime, duration_min: int,
                                attendees: list[str], notes: str | None) -> CalendarEvent
        """
        # Should not raise TypeError
        result = calendar_tool.create_event(
            city="Taipei",
            dt=datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc),
            duration_min=60,
            attendees=["Alice", "Bob"],
            notes="Test meeting"
        )

        assert isinstance(result, CalendarEvent), "Should return CalendarEvent"

        # Test with notes=None
        result2 = calendar_tool.create_event(
            city="Tokyo",
            dt=datetime(2025, 10, 18, 10, 0, tzinfo=timezone.utc),
            duration_min=30,
            attendees=["Charlie"],
            notes=None
        )

        assert isinstance(result2, CalendarEvent), "Should handle notes=None"


@pytest.mark.parametrize("dt,duration_min", [
    (datetime(2025, 10, 17, 14, 0, tzinfo=timezone.utc), 60),
    (datetime(2025, 10, 20, 10, 0, tzinfo=timezone.utc), 30),
    (datetime(2025, 11, 1, 12, 0, tzinfo=timezone.utc), 90),
])
def test_calendar_tool_consistency(dt, duration_min):
    """
    Test that MockCalendarTool produces consistent results for the same inputs.

    Contract requirement: Deterministic behavior for testing.
    """
    tool = MockCalendarTool()

    result1 = tool.find_free_slot(dt, duration_min)
    result2 = tool.find_free_slot(dt, duration_min)

    # Same inputs should produce same outputs in mock mode
    assert result1["status"] == result2["status"], "Should be deterministic"
    assert len(result1["candidates"]) == len(result2["candidates"]), "Should be deterministic"
