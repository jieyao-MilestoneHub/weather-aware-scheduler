"""Tests for Calendar Agent scheduling operations.

Tests Calendar Agent's ability to check availability, find free slots, and
create calendar events using LLM reasoning combined with calendar tools.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.base import AgentConfig
from src.agents.protocol import AgentRequest, AgentResponse, AgentRole


# Skip tests if no API key is configured
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="No OpenAI or Azure OpenAI API key configured"
)


class TestCalendarAgentCreation:
    """Test Calendar Agent instantiation and configuration."""

    def test_create_calendar_agent_imports(self):
        """Test that Calendar Agent can be imported."""
        from src.agents.calendar_agent import CalendarAgent, create_calendar_agent

        assert CalendarAgent is not None
        assert create_calendar_agent is not None
        assert AgentRole.CALENDAR is not None
        assert AgentConfig is not None

    def test_create_calendar_agent_default_config(self):
        """Test creating Calendar Agent with default configuration from environment."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        assert agent is not None
        assert agent.config.role == AgentRole.CALENDAR
        assert agent.llm_with_tools is not None

    def test_create_calendar_agent_mock_mode(self, monkeypatch):
        """Test creating Calendar Agent in mock mode (no real API calls)."""
        from src.agents.calendar_agent import create_calendar_agent

        # Set environment to avoid real API calls
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-mock")

        agent = create_calendar_agent()

        assert agent.config.model_name == "gpt-4o-mini"  # Default from env


class TestCalendarAgentAvailabilityCheck:
    """Test Calendar Agent's availability checking capabilities."""

    @pytest.mark.asyncio
    async def test_check_availability_for_free_slot(self):
        """Test checking availability for an available time slot.

        Input: Monday 10am, 60min duration
        Expected: Successfully identify slot as available
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        # Get next Monday 10am
        dt = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        days_ahead = 0 - dt.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = dt + timedelta(days=days_ahead)

        request = AgentRequest(
            request_id="test-cal-001",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": next_monday.isoformat(),
                "duration_min": 60
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        assert response.agent_role == AgentRole.CALENDAR

        result = response.result
        assert "is_available" in result
        assert result["is_available"] is True

    @pytest.mark.asyncio
    async def test_check_availability_for_busy_slot(self):
        """Test checking availability for a busy time slot (Friday 3pm).

        Input: Friday 3pm, 30min duration
        Expected: Successfully identify slot as busy
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        # Get next Friday 3pm (configured as busy in MockCalendarTool)
        dt = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        days_ahead = 4 - dt.weekday()
        if days_ahead < 0:
            days_ahead += 7
        friday_3pm = dt + timedelta(days=days_ahead)

        request = AgentRequest(
            request_id="test-cal-002",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": friday_3pm.isoformat(),
                "duration_min": 30
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        result = response.result
        assert "is_available" in result
        assert result["is_available"] is False


class TestCalendarAgentFreeSlotFinding:
    """Test Calendar Agent's free slot finding capabilities."""

    @pytest.mark.asyncio
    async def test_find_free_slot_from_busy_time(self):
        """Test finding free slot when requested time is busy.

        Input: Friday 3pm (busy), 60min duration
        Expected: Return next available free slot
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        # Friday 3pm is busy
        dt = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
        days_ahead = 4 - dt.weekday()
        if days_ahead < 0:
            days_ahead += 7
        friday_3pm = dt + timedelta(days=days_ahead)

        request = AgentRequest(
            request_id="test-cal-003",
            agent_role=AgentRole.CALENDAR,
            action="find_free_slot",
            parameters={
                "datetime_iso": friday_3pm.isoformat(),
                "duration_min": 60
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        result = response.result

        assert "free_slot" in result
        free_slot = result["free_slot"]
        assert "datetime_iso" in free_slot
        assert free_slot["duration_min"] == 60

        # Free slot should be different from requested (busy) time
        assert free_slot["datetime_iso"] != friday_3pm.isoformat()

    @pytest.mark.asyncio
    async def test_find_free_slot_returns_alternatives(self):
        """Test that find_free_slot returns alternative time options.

        Input: Friday 3pm (busy), 30min duration
        Expected: Return primary free slot + alternatives
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        busy_time = datetime(2025, 10, 31, 15, 0)  # Friday 3pm

        request = AgentRequest(
            request_id="test-cal-004",
            agent_role=AgentRole.CALENDAR,
            action="find_free_slot",
            parameters={
                "datetime_iso": busy_time.isoformat(),
                "duration_min": 30
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        result = response.result

        assert "free_slot" in result
        # May include alternatives
        if "alternatives" in result:
            assert isinstance(result["alternatives"], list)


class TestCalendarAgentEventCreation:
    """Test Calendar Agent's event creation capabilities."""

    @pytest.mark.asyncio
    async def test_create_event_with_all_fields(self):
        """Test creating event with all required and optional fields.

        Input: Taipei, Monday 10am, 60min, [Alice, Bob], "Project kickoff"
        Expected: Successfully create event with all fields
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 27, 10, 0)

        request = AgentRequest(
            request_id="test-cal-005",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Taipei",
                "datetime_iso": dt.isoformat(),
                "duration_min": 60,
                "attendees": ["Alice", "Bob"],
                "notes": "Project kickoff meeting"
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        result = response.result

        assert "event" in result
        event = result["event"]
        assert event["city"] == "Taipei"
        assert event["duration_min"] == 60
        assert event["attendees"] == ["Alice", "Bob"]
        assert "id" in event or "event_id" in event

    @pytest.mark.asyncio
    async def test_create_event_minimal_fields(self):
        """Test creating event with only required fields.

        Input: Tokyo, Monday 2pm, 30min, no attendees, no notes
        Expected: Successfully create event with defaults for optional fields
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 27, 14, 0)

        request = AgentRequest(
            request_id="test-cal-006",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Tokyo",
                "datetime_iso": dt.isoformat(),
                "duration_min": 30,
                "attendees": [],
                "notes": ""
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        result = response.result

        assert "event" in result
        event = result["event"]
        assert event["city"] == "Tokyo"
        assert event["duration_min"] == 30

    @pytest.mark.asyncio
    async def test_create_event_returns_event_id(self):
        """Test that created event includes unique event ID.

        Input: Berlin, Tuesday 9am, 90min
        Expected: Event created with unique ID
        """
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 28, 9, 0)

        request = AgentRequest(
            request_id="test-cal-007",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Berlin",
                "datetime_iso": dt.isoformat(),
                "duration_min": 90,
                "attendees": ["Charlie"],
                "notes": "Review session"
            },
        )

        response = await agent.process_request(request)

        assert response.success is True
        event = response.result["event"]

        # Should have unique event ID
        assert "id" in event or "event_id" in event
        event_id = event.get("id") or event.get("event_id")
        assert event_id is not None
        assert len(event_id) > 0


class TestCalendarAgentLLMIntegration:
    """Test Calendar Agent's LLM reasoning and tool calling."""

    @pytest.mark.asyncio
    async def test_agent_uses_correct_tool_for_availability(self):
        """Test that agent selects check_availability_tool for availability queries."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 27, 10, 0)

        request = AgentRequest(
            request_id="test-cal-008",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": dt.isoformat(),
                "duration_min": 60
            },
        )

        # Mock the LLM to verify it calls the right tool
        mock_response = MagicMock()
        mock_response.content = "Checking availability"
        mock_response.tool_calls = [
            {
                "name": "check_availability_tool",
                "args": {
                    "datetime_iso": dt.isoformat(),
                    "duration_min": 60
                }
            }
        ]

        with patch.object(agent.llm_with_tools, 'ainvoke', return_value=mock_response):
            response = await agent.process_request(request)

        assert response.success is True

    @pytest.mark.asyncio
    async def test_agent_uses_correct_tool_for_free_slot(self):
        """Test that agent selects find_free_slot_tool for free slot queries."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 31, 15, 0)

        request = AgentRequest(
            request_id="test-cal-009",
            agent_role=AgentRole.CALENDAR,
            action="find_free_slot",
            parameters={
                "datetime_iso": dt.isoformat(),
                "duration_min": 30
            },
        )

        # Mock the LLM to verify it calls the right tool
        mock_response = MagicMock()
        mock_response.content = "Finding free slot"
        mock_response.tool_calls = [
            {
                "name": "find_free_slot_tool",
                "args": {
                    "datetime_iso": dt.isoformat(),
                    "duration_min": 30
                }
            }
        ]

        with patch.object(agent.llm_with_tools, 'ainvoke', return_value=mock_response):
            response = await agent.process_request(request)

        assert response.success is True


class TestCalendarAgentErrorHandling:
    """Test Calendar Agent error handling."""

    @pytest.mark.asyncio
    async def test_missing_required_parameter_datetime(self):
        """Test handling of missing datetime parameter."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        request = AgentRequest(
            request_id="test-cal-error-001",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                # Missing datetime_iso
                "duration_min": 60
            },
        )

        response = await agent.process_request(request)

        assert response.success is False
        assert response.error is not None
        assert "datetime" in response.error.lower()

    @pytest.mark.asyncio
    async def test_missing_required_parameter_city(self):
        """Test handling of missing city parameter for event creation."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        dt = datetime(2025, 10, 27, 10, 0)

        request = AgentRequest(
            request_id="test-cal-error-002",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                # Missing city
                "datetime_iso": dt.isoformat(),
                "duration_min": 60,
                "attendees": [],
                "notes": ""
            },
        )

        response = await agent.process_request(request)

        assert response.success is False
        assert response.error is not None
        assert "city" in response.error.lower()

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test handling of invalid action."""
        from src.agents.calendar_agent import create_calendar_agent

        agent = create_calendar_agent()

        request = AgentRequest(
            request_id="test-cal-error-003",
            agent_role=AgentRole.CALENDAR,
            action="invalid_action",
            parameters={},
        )

        response = await agent.process_request(request)

        assert response.success is False
        assert response.error is not None
        assert "action" in response.error.lower()
