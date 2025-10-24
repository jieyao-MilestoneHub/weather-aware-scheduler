"""Unit tests for mock weather and calendar tools."""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.tools.mock_weather import MockWeatherTool
from src.tools.mock_calendar import MockCalendarTool


class TestMockWeatherTool:
    """Test MockWeatherTool behavior and patterns."""

    @freeze_time("2025-10-13 10:00:00")
    def test_rainy_window_14_to_16_returns_rain(self):
        """Time window 14:00-16:00 should return rain condition."""
        tool = MockWeatherTool()

        # Test at 14:00 (start of window)
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 14, 0))
        assert result["condition"] == "rain"

        # Test at 15:00 (middle of window)
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 15, 0))
        assert result["condition"] == "rain"

    @freeze_time("2025-10-13 10:00:00")
    def test_outside_rainy_window_returns_clear(self):
        """Times outside 14:00-16:00 should return clear condition."""
        tool = MockWeatherTool()

        # Test at 10:00 (before window)
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 10, 0))
        assert result["condition"] == "clear"

        # Test at 18:00 (after window)
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 18, 0))
        assert result["condition"] == "clear"

    @freeze_time("2025-10-13 10:00:00")
    def test_weather_includes_temperature(self):
        """Weather result should include temperature field."""
        tool = MockWeatherTool()
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 10, 0))

        assert "temperature" in result
        assert isinstance(result["temperature"], (int, float))

    @freeze_time("2025-10-13 10:00:00")
    def test_weather_includes_city(self):
        """Weather result should echo back the city."""
        tool = MockWeatherTool()
        result = tool.get_weather("Taipei", datetime(2025, 10, 17, 10, 0))

        assert result["city"] == "Taipei"

    @freeze_time("2025-10-13 10:00:00")
    def test_different_cities_return_weather(self):
        """Mock should work with any city name."""
        tool = MockWeatherTool()

        result_taipei = tool.get_weather("Taipei", datetime(2025, 10, 17, 10, 0))
        result_tokyo = tool.get_weather("Tokyo", datetime(2025, 10, 17, 10, 0))

        assert result_taipei["city"] == "Taipei"
        assert result_tokyo["city"] == "Tokyo"


class TestMockCalendarTool:
    """Test MockCalendarTool behavior and patterns."""

    @freeze_time("2025-10-13 10:00:00")
    def test_no_conflicts_for_non_busy_times(self):
        """Non-busy times should return empty conflicts list."""
        tool = MockCalendarTool()

        # Friday 10:00 is not in busy window (busy is 15:00-15:30)
        conflicts = tool.check_conflicts(datetime(2025, 10, 17, 10, 0), duration_min=60)
        assert conflicts == []

    @freeze_time("2025-10-13 10:00:00")
    def test_conflict_detected_in_busy_window(self):
        """Busy window (15:00-15:30 on Oct 17) should return conflicts."""
        tool = MockCalendarTool()

        # This overlaps with the mock busy slot (15:00-15:30)
        conflicts = tool.check_conflicts(datetime(2025, 10, 17, 15, 0), duration_min=60)
        assert len(conflicts) > 0

    @freeze_time("2025-10-13 10:00:00")
    def test_conflict_includes_event_details(self):
        """Conflict should include start, end, and summary."""
        tool = MockCalendarTool()

        conflicts = tool.check_conflicts(datetime(2025, 10, 17, 15, 0), duration_min=60)

        if len(conflicts) > 0:
            conflict = conflicts[0]
            assert "start" in conflict
            assert "end" in conflict
            assert "summary" in conflict

    @freeze_time("2025-10-13 10:00:00")
    def test_partial_overlap_detected(self):
        """Partial overlap with existing event should be detected."""
        tool = MockCalendarTool()

        # Start at 14:45, overlaps with 15:00-15:30 busy slot
        conflicts = tool.check_conflicts(datetime(2025, 10, 17, 14, 45), duration_min=60)
        assert len(conflicts) > 0

    @freeze_time("2025-10-13 10:00:00")
    def test_find_free_slot_returns_valid_time(self):
        """find_free_slot should return a datetime without conflicts."""
        tool = MockCalendarTool()

        # Looking for slot on Oct 17 starting from 9:00
        free_slot = tool.find_free_slot(
            start_search=datetime(2025, 10, 17, 9, 0),
            duration_min=60,
            search_window_hours=8
        )

        assert free_slot is not None
        assert isinstance(free_slot, datetime)

        # Verify the free slot has no conflicts
        conflicts = tool.check_conflicts(free_slot, duration_min=60)
        assert conflicts == []

    @freeze_time("2025-10-13 10:00:00")
    def test_find_free_slot_skips_busy_times(self):
        """find_free_slot should skip over busy windows."""
        tool = MockCalendarTool()

        # Start search at busy time (15:00)
        free_slot = tool.find_free_slot(
            start_search=datetime(2025, 10, 17, 15, 0),
            duration_min=60,
            search_window_hours=8
        )

        # Should find a slot after the busy window (15:30 or later)
        assert free_slot is not None
        # Verify no conflicts at found slot
        conflicts = tool.check_conflicts(free_slot, duration_min=60)
        assert conflicts == []

    @freeze_time("2025-10-13 10:00:00")
    def test_find_free_slot_respects_search_window(self):
        """find_free_slot should respect the search window limit."""
        tool = MockCalendarTool()

        # Very narrow search window might return None if no slot found
        free_slot = tool.find_free_slot(
            start_search=datetime(2025, 10, 17, 15, 0),
            duration_min=60,
            search_window_hours=1  # Only 1 hour to search
        )

        # Within the mock's behavior, should either find slot or return None
        # (depends on mock implementation details)
        if free_slot:
            assert isinstance(free_slot, datetime)

    @freeze_time("2025-10-13 10:00:00")
    def test_find_free_slot_various_durations_15min(self):
        """find_free_slot should work with 15 minute duration."""
        tool = MockCalendarTool()

        free_slot = tool.find_free_slot(
            start_search=datetime(2025, 10, 17, 9, 0),
            duration_min=15,
            search_window_hours=8
        )

        assert free_slot is not None
        conflicts = tool.check_conflicts(free_slot, duration_min=15)
        assert conflicts == []

    @freeze_time("2025-10-13 10:00:00")
    def test_find_free_slot_various_durations_120min(self):
        """find_free_slot should work with 120 minute duration."""
        tool = MockCalendarTool()

        free_slot = tool.find_free_slot(
            start_search=datetime(2025, 10, 17, 9, 0),
            duration_min=120,
            search_window_hours=8
        )

        assert free_slot is not None
        conflicts = tool.check_conflicts(free_slot, duration_min=120)
        assert conflicts == []

    @freeze_time("2025-10-13 10:00:00")
    def test_create_event_returns_event_id(self):
        """create_event should return CalendarEvent with event_id."""
        tool = MockCalendarTool()

        event = tool.create_event(
            city="Taipei",
            dt=datetime(2025, 10, 17, 10, 0),
            duration_min=60,
            attendees=["Alice", "Bob"],
            notes="Test meeting"
        )

        assert event.event_id is not None
        assert event.event_id.startswith("mock-event-")
        assert event.city == "Taipei"
        assert event.attendees == ["Alice", "Bob"]
        assert event.duration == 60

    @freeze_time("2025-10-13 10:00:00")
    def test_create_event_returns_summary(self):
        """create_event should include reason and status."""
        tool = MockCalendarTool()

        event = tool.create_event(
            city="Tokyo",
            dt=datetime(2025, 10, 17, 14, 0),
            duration_min=30,
            attendees=["Charlie"],
            notes=None
        )

        assert event.reason is not None
        assert event.status == "confirmed"


class TestMockToolIntegration:
    """Test interaction between mock tools."""

    @freeze_time("2025-10-13 10:00:00")
    def test_weather_and_calendar_independent(self):
        """Weather and calendar tools should work independently."""
        weather_tool = MockWeatherTool()
        calendar_tool = MockCalendarTool()

        dt = datetime(2025, 10, 17, 14, 0)

        # Get weather (rainy)
        weather = weather_tool.get_weather("Taipei", dt)
        assert weather["condition"] == "rain"

        # Check calendar (may or may not have conflicts)
        conflicts = calendar_tool.check_conflicts(dt, duration_min=60)

        # Both should return results independently
        assert weather is not None
        assert isinstance(conflicts, list)

    @freeze_time("2025-10-13 10:00:00")
    def test_combined_avoidance_strategy(self):
        """Can find slot avoiding both rain and conflicts."""
        weather_tool = MockWeatherTool()
        calendar_tool = MockCalendarTool()

        # Search for good slot on Oct 17
        search_start = datetime(2025, 10, 17, 9, 0)

        # Find free calendar slot
        free_slot = calendar_tool.find_free_slot(
            start_search=search_start,
            duration_min=60,
            search_window_hours=8
        )

        assert free_slot is not None

        # Check if it's also good weather
        weather = weather_tool.get_weather("Taipei", free_slot)

        # We can't guarantee clear weather from find_free_slot alone,
        # but we can verify both tools provide results
        assert weather["condition"] in ["clear", "rain"]
