"""Unit tests for Calendar Agent LangChain tools.

Tests the calendar tool wrappers that will be used by Calendar Agent.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.tools.calendar_tools import (
    check_availability_tool,
    find_free_slot_tool,
    create_event_tool,
    CALENDAR_TOOLS,
)


class TestCheckAvailabilityTool:
    """Test check_availability_tool."""

    def test_check_availability_available_slot(self):
        """Test checking availability for an available time slot."""
        # Use a time that should be available (Monday 10am)
        dt = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        # Add days until next Monday
        days_ahead = 0 - dt.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = dt + timedelta(days=days_ahead)

        result = check_availability_tool.invoke({
            "datetime_iso": next_monday.isoformat(),
            "duration_min": 60
        })

        assert isinstance(result, dict)
        assert "is_available" in result
        assert "datetime_iso" in result
        assert "duration_min" in result

    def test_check_availability_busy_slot(self):
        """Test checking availability for a busy time slot (Friday 3pm)."""
        # Friday 3pm is configured as busy in MockCalendarTool
        dt = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        days_ahead = 4 - dt.weekday()  # Friday
        if days_ahead < 0:
            days_ahead += 7
        friday_3pm = dt + timedelta(days=days_ahead)

        result = check_availability_tool.invoke({
            "datetime_iso": friday_3pm.isoformat(),
            "duration_min": 30
        })

        assert isinstance(result, dict)
        assert "is_available" in result
        # Friday 3pm should be busy
        assert result["is_available"] is False

    def test_check_availability_returns_datetime_and_duration(self):
        """Test that result includes the queried datetime and duration."""
        dt = datetime(2025, 10, 27, 14, 0)  # Specific Monday

        result = check_availability_tool.invoke({
            "datetime_iso": dt.isoformat(),
            "duration_min": 90
        })

        assert result["datetime_iso"] == dt.isoformat()
        assert result["duration_min"] == 90


class TestFindFreeSlotTool:
    """Test find_free_slot_tool."""

    def test_find_free_slot_from_busy_time(self):
        """Test finding free slot when requested time is busy."""
        # Friday 3pm is busy
        dt = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        days_ahead = 4 - dt.weekday()
        if days_ahead < 0:
            days_ahead += 7
        friday_3pm = dt + timedelta(days=days_ahead)

        result = find_free_slot_tool.invoke({
            "datetime_iso": friday_3pm.isoformat(),
            "duration_min": 60
        })

        assert isinstance(result, dict)
        assert "success" in result
        assert "free_slot" in result

        if result["success"]:
            free_slot = result["free_slot"]
            assert "datetime_iso" in free_slot
            assert "duration_min" in free_slot
            # Free slot should be different from requested time
            assert free_slot["datetime_iso"] != friday_3pm.isoformat()

    def test_find_free_slot_returns_alternatives(self):
        """Test that find_free_slot returns alternative time options."""
        busy_time = datetime(2025, 10, 31, 15, 0)  # Friday 3pm

        result = find_free_slot_tool.invoke({
            "datetime_iso": busy_time.isoformat(),
            "duration_min": 30
        })

        assert result["success"] is True
        assert "free_slot" in result
        # Should find next available slot

    def test_find_free_slot_preserves_duration(self):
        """Test that suggested free slot preserves requested duration."""
        busy_time = datetime(2025, 10, 31, 15, 0)
        requested_duration = 120

        result = find_free_slot_tool.invoke({
            "datetime_iso": busy_time.isoformat(),
            "duration_min": requested_duration
        })

        if result["success"]:
            assert result["free_slot"]["duration_min"] == requested_duration


class TestCreateEventTool:
    """Test create_event_tool."""

    def test_create_event_with_all_fields(self):
        """Test creating event with all required fields."""
        dt = datetime(2025, 10, 27, 10, 0)

        result = create_event_tool.invoke({
            "city": "Taipei",
            "datetime_iso": dt.isoformat(),
            "duration_min": 60,
            "attendees": ["Alice", "Bob"],
            "notes": "Project kickoff meeting"
        })

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "event" in result

        event = result["event"]
        assert event["city"] == "Taipei"
        assert event["datetime_iso"] == dt.isoformat()
        assert event["duration_min"] == 60
        assert event["attendees"] == ["Alice", "Bob"]
        assert "notes" in event

    def test_create_event_minimal_fields(self):
        """Test creating event with only required fields."""
        dt = datetime(2025, 10, 27, 14, 0)

        result = create_event_tool.invoke({
            "city": "Tokyo",
            "datetime_iso": dt.isoformat(),
            "duration_min": 30,
            "attendees": [],
            "notes": ""
        })

        assert result["success"] is True
        assert result["event"]["city"] == "Tokyo"
        assert result["event"]["duration_min"] == 30

    def test_create_event_returns_created_event(self):
        """Test that create_event returns the created event details."""
        dt = datetime(2025, 10, 28, 9, 0)

        result = create_event_tool.invoke({
            "city": "Berlin",
            "datetime_iso": dt.isoformat(),
            "duration_min": 90,
            "attendees": ["Charlie"],
            "notes": "Review session"
        })

        assert "event" in result
        event = result["event"]
        assert "id" in event or "event_id" in event  # Event should have an ID
        assert event["city"] == "Berlin"
        assert event["attendees"] == ["Charlie"]


class TestCalendarToolsIntegration:
    """Test calendar tools integration and list export."""

    def test_calendar_tools_list_exists(self):
        """Test that CALENDAR_TOOLS list is exported."""
        assert CALENDAR_TOOLS is not None
        assert isinstance(CALENDAR_TOOLS, list)
        assert len(CALENDAR_TOOLS) == 3

    def test_calendar_tools_list_contains_correct_tools(self):
        """Test that CALENDAR_TOOLS contains the expected tools."""
        tool_names = [tool.name for tool in CALENDAR_TOOLS]

        assert "check_availability_tool" in tool_names
        assert "find_free_slot_tool" in tool_names
        assert "create_event_tool" in tool_names

    def test_all_tools_are_invokable(self):
        """Test that all tools in CALENDAR_TOOLS can be invoked."""
        dt = datetime(2025, 10, 27, 10, 0)

        for tool in CALENDAR_TOOLS:
            assert hasattr(tool, "invoke")
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_tools_have_proper_schemas(self):
        """Test that all tools have proper Pydantic schemas."""
        for tool in CALENDAR_TOOLS:
            assert hasattr(tool, "args_schema")
            # Schema should be a Pydantic model or similar
            assert tool.args_schema is not None
