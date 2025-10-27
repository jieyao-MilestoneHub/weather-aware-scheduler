"""Integration test for US1 - Simple Schedule Creation (Multi-Agent Architecture).

Tests the complete multi-agent workflow for simple scheduling:
1. Parser Agent extracts scheduling info from natural language
2. Calendar Agent checks availability and creates event
3. Orchestrator coordinates the agents and returns result

This test validates the MVP functionality (Phase 3 / US1).
"""

import os
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.protocol import AgentRequest, AgentResponse, AgentRole


# Skip tests if Calendar Agent not yet implemented
pytestmark = pytest.mark.skip(reason="US1 multi-agent workflow not yet implemented - pending T013-T016")


class TestUS1SimpleSchedulingWorkflow:
    """End-to-end tests for US1 - Simple Schedule Creation using Multi-Agent Architecture."""

    @freeze_time("2025-10-13 10:00:00")  # Monday morning
    @pytest.mark.asyncio
    async def test_complete_scheduling_workflow_success(self):
        """Test complete workflow: parse input → check availability → create event.

        Input: "Friday 10am Taipei meet Alice 60min"
        Expected Flow:
        1. Parser Agent extracts: city=Taipei, datetime=Oct 17 10:00, duration=60, attendees=[Alice]
        2. Calendar Agent checks Friday 10am is available
        3. Calendar Agent creates event
        4. Orchestrator returns confirmed event

        This is the golden path for US1.
        """
        from src.agents.parser_agent import create_parser_agent
        from src.agents.calendar_agent import create_calendar_agent

        parser_agent = create_parser_agent()
        calendar_agent = create_calendar_agent()

        # Step 1: Parse natural language input
        parse_request = AgentRequest(
            request_id="us1-test-001-parse",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "Friday 10am Taipei meet Alice 60min"},
        )

        parse_response = await parser_agent.process_request(parse_request)

        assert parse_response.success is True
        assert "extracted_data" in parse_response.result
        extracted = parse_response.result["extracted_data"]

        assert extracted["city"] == "Taipei"
        assert "Friday" in extracted.get("datetime_str", "") or extracted.get("datetime_iso")
        assert extracted["duration_minutes"] == 60
        assert "Alice" in extracted.get("attendees", [])

        # Step 2: Check availability with Calendar Agent
        # Calculate Friday 10am from frozen time (Monday 10am)
        current_time = datetime(2025, 10, 13, 10, 0)
        friday_10am = current_time + timedelta(days=4)  # Friday Oct 17

        availability_request = AgentRequest(
            request_id="us1-test-001-availability",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": friday_10am.isoformat(),
                "duration_min": 60
            },
        )

        availability_response = await calendar_agent.process_request(availability_request)

        assert availability_response.success is True
        assert availability_response.result["is_available"] is True

        # Step 3: Create event with Calendar Agent
        create_event_request = AgentRequest(
            request_id="us1-test-001-create",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Taipei",
                "datetime_iso": friday_10am.isoformat(),
                "duration_min": 60,
                "attendees": ["Alice"],
                "notes": "Team meeting"
            },
        )

        create_event_response = await calendar_agent.process_request(create_event_request)

        assert create_event_response.success is True
        event = create_event_response.result["event"]

        # Verify event details
        assert event["city"] == "Taipei"
        assert event["duration_min"] == 60
        assert event["attendees"] == ["Alice"]
        assert "id" in event or "event_id" in event
        assert event.get("status") == "confirmed"

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_scheduling_workflow_with_conflict_resolution(self):
        """Test workflow when requested time is busy - find alternative.

        Input: "Friday 3pm Taipei meet Bob 30min"
        Expected Flow:
        1. Parser Agent extracts: city=Taipei, datetime=Oct 17 15:00, duration=30, attendees=[Bob]
        2. Calendar Agent finds Friday 3pm is BUSY (mock conflict)
        3. Calendar Agent finds next free slot (Friday 3:30pm)
        4. Calendar Agent creates event at alternative time
        5. Orchestrator returns event with note about time adjustment

        This tests conflict resolution (FR-015).
        """
        from src.agents.parser_agent import create_parser_agent
        from src.agents.calendar_agent import create_calendar_agent

        parser_agent = create_parser_agent()
        calendar_agent = create_calendar_agent()

        # Step 1: Parse input
        parse_request = AgentRequest(
            request_id="us1-test-002-parse",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "Friday 3pm Taipei meet Bob 30min"},
        )

        parse_response = await parser_agent.process_request(parse_request)
        assert parse_response.success is True

        # Step 2: Check availability (should be busy - Friday 3pm)
        current_time = datetime(2025, 10, 13, 10, 0)
        friday_3pm = current_time + timedelta(days=4, hours=5)  # Friday Oct 17, 15:00

        availability_request = AgentRequest(
            request_id="us1-test-002-availability",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": friday_3pm.isoformat(),
                "duration_min": 30
            },
        )

        availability_response = await calendar_agent.process_request(availability_request)

        assert availability_response.success is True
        assert availability_response.result["is_available"] is False
        assert "reason" in availability_response.result

        # Step 3: Find free slot
        find_free_request = AgentRequest(
            request_id="us1-test-002-find-free",
            agent_role=AgentRole.CALENDAR,
            action="find_free_slot",
            parameters={
                "datetime_iso": friday_3pm.isoformat(),
                "duration_min": 30
            },
        )

        find_free_response = await calendar_agent.process_request(find_free_request)

        assert find_free_response.success is True
        assert "free_slot" in find_free_response.result

        free_slot = find_free_response.result["free_slot"]
        assert free_slot["datetime_iso"] != friday_3pm.isoformat()  # Different from requested
        assert free_slot["duration_min"] == 30

        # Step 4: Create event at free slot
        create_event_request = AgentRequest(
            request_id="us1-test-002-create",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Taipei",
                "datetime_iso": free_slot["datetime_iso"],
                "duration_min": 30,
                "attendees": ["Bob"],
                "notes": "Rescheduled from 3pm due to conflict"
            },
        )

        create_event_response = await calendar_agent.process_request(create_event_request)

        assert create_event_response.success is True
        event = create_event_response.result["event"]
        assert event["city"] == "Taipei"
        assert event["attendees"] == ["Bob"]

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_scheduling_workflow_minimal_input(self):
        """Test workflow with minimal input (no attendees, default description).

        Input: "Monday 2pm Tokyo 45min"
        Expected Flow:
        1. Parser Agent extracts: city=Tokyo, datetime=Oct 20 14:00, duration=45, attendees=[]
        2. Calendar Agent checks availability
        3. Calendar Agent creates event with empty attendees
        4. Orchestrator returns confirmed event

        This tests handling of optional fields (FR-012, FR-013).
        """
        from src.agents.parser_agent import create_parser_agent
        from src.agents.calendar_agent import create_calendar_agent

        parser_agent = create_parser_agent()
        calendar_agent = create_calendar_agent()

        # Step 1: Parse minimal input
        parse_request = AgentRequest(
            request_id="us1-test-003-parse",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "Monday 2pm Tokyo 45min"},
        )

        parse_response = await parser_agent.process_request(parse_request)

        assert parse_response.success is True
        extracted = parse_response.result["extracted_data"]

        assert extracted["city"] == "Tokyo"
        assert extracted["duration_minutes"] == 45
        # Attendees may be empty or not present
        attendees = extracted.get("attendees", [])
        assert isinstance(attendees, list)

        # Step 2: Create event with minimal fields
        current_time = datetime(2025, 10, 13, 10, 0)
        next_monday = current_time + timedelta(days=7, hours=4)  # Monday Oct 20, 14:00

        create_event_request = AgentRequest(
            request_id="us1-test-003-create",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Tokyo",
                "datetime_iso": next_monday.isoformat(),
                "duration_min": 45,
                "attendees": [],
                "notes": ""
            },
        )

        create_event_response = await calendar_agent.process_request(create_event_request)

        assert create_event_response.success is True
        event = create_event_response.result["event"]

        assert event["city"] == "Tokyo"
        assert event["duration_min"] == 45
        assert event["attendees"] == []

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_scheduling_workflow_with_multiple_attendees(self):
        """Test workflow with multiple attendees.

        Input: "Wednesday 11am Berlin meet Alice, Bob, Charlie 90min"
        Expected Flow:
        1. Parser Agent extracts: city=Berlin, attendees=[Alice, Bob, Charlie], duration=90
        2. Calendar Agent creates event with all attendees
        3. Event should include all three attendees

        This tests attendee parsing and handling (FR-013).
        """
        from src.agents.parser_agent import create_parser_agent
        from src.agents.calendar_agent import create_calendar_agent

        parser_agent = create_parser_agent()
        calendar_agent = create_calendar_agent()

        # Step 1: Parse input with multiple attendees
        parse_request = AgentRequest(
            request_id="us1-test-004-parse",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "Wednesday 11am Berlin meet Alice, Bob, Charlie 90min"},
        )

        parse_response = await parser_agent.process_request(parse_request)

        assert parse_response.success is True
        extracted = parse_response.result["extracted_data"]

        assert extracted["city"] == "Berlin"
        assert extracted["duration_minutes"] == 90
        attendees = extracted.get("attendees", [])
        assert len(attendees) == 3
        assert "Alice" in attendees
        assert "Bob" in attendees
        assert "Charlie" in attendees

        # Step 2: Create event with multiple attendees
        current_time = datetime(2025, 10, 13, 10, 0)
        wednesday_11am = current_time + timedelta(days=2, hours=1)  # Wednesday Oct 15, 11:00

        create_event_request = AgentRequest(
            request_id="us1-test-004-create",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": "Berlin",
                "datetime_iso": wednesday_11am.isoformat(),
                "duration_min": 90,
                "attendees": ["Alice", "Bob", "Charlie"],
                "notes": "Team meeting"
            },
        )

        create_event_response = await calendar_agent.process_request(create_event_request)

        assert create_event_response.success is True
        event = create_event_response.result["event"]

        assert event["attendees"] == ["Alice", "Bob", "Charlie"]
        assert len(event["attendees"]) == 3


class TestUS1OrchestratorIntegration:
    """Test Orchestrator coordination for US1 workflow."""

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_orchestrator_coordinates_parser_and_calendar(self):
        """Test that Orchestrator correctly coordinates Parser and Calendar agents.

        Input: "Thursday 3pm Paris 60min"
        Expected:
        1. Orchestrator sends request to Parser Agent
        2. Orchestrator receives parsed data
        3. Orchestrator sends request to Calendar Agent
        4. Orchestrator receives created event
        5. Orchestrator returns final result to user
        """
        # This test will be implemented when Orchestrator is created in T014
        pytest.skip("Orchestrator not yet implemented - pending T014")

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_orchestrator_handles_incomplete_parse(self):
        """Test Orchestrator handles incomplete parsing (missing required fields).

        Input: "meet Alice" (missing time, location, duration)
        Expected:
        1. Orchestrator sends to Parser Agent
        2. Parser identifies missing: datetime, city, duration
        3. Orchestrator returns clarification request to user
        4. No Calendar Agent call made
        """
        # This test will be implemented when Orchestrator is created in T014
        pytest.skip("Orchestrator not yet implemented - pending T014")

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_orchestrator_handles_calendar_error(self):
        """Test Orchestrator handles Calendar Agent errors gracefully.

        Scenario: Calendar service unavailable
        Expected:
        1. Orchestrator sends to Parser Agent (success)
        2. Orchestrator sends to Calendar Agent (error)
        3. Orchestrator returns error message to user
        """
        # This test will be implemented when Orchestrator is created in T014
        pytest.skip("Orchestrator not yet implemented - pending T014")


class TestUS1CLIIntegration:
    """Test CLI integration for US1 (multi-agent mode)."""

    @freeze_time("2025-10-13 10:00:00")
    def test_cli_multi_agent_mode_simple_scheduling(self):
        """Test CLI in multi-agent mode for simple scheduling.

        Command: schedule --mode multi_agent "Friday 2pm London meet Dave 45min"
        Expected:
        - CLI routes to Orchestrator
        - Orchestrator coordinates Parser + Calendar agents
        - CLI displays formatted event confirmation
        """
        # This test will be implemented when CLI is updated in T015
        pytest.skip("CLI multi-agent mode not yet implemented - pending T015")

    @freeze_time("2025-10-13 10:00:00")
    def test_cli_multi_agent_mode_env_variable(self):
        """Test CLI uses AGENT_MODE environment variable.

        Environment: AGENT_MODE=multi_agent
        Command: schedule "Friday 2pm London meet Dave 45min"
        Expected:
        - CLI detects multi_agent mode from environment
        - Routes to Orchestrator instead of LangGraph
        """
        # This test will be implemented when CLI is updated in T015
        pytest.skip("CLI multi-agent mode not yet implemented - pending T015")


class TestUS1PerformanceAndEdgeCases:
    """Test performance requirements and edge cases for US1."""

    @pytest.mark.asyncio
    async def test_scheduling_workflow_performance_under_2s(self):
        """Test that simple scheduling completes in under 2 seconds (NFR-001).

        Input: "Monday 10am Tokyo 30min"
        Expected: Complete workflow in < 2000ms
        """
        import time

        # This test will be implemented when full workflow is ready
        pytest.skip("Full workflow not yet implemented - pending T014")

        # Pseudo-code for actual implementation:
        # start = time.time()
        # result = await orchestrator.schedule("Monday 10am Tokyo 30min")
        # duration = time.time() - start
        # assert duration < 2.0

    @freeze_time("2025-10-13 10:00:00")
    @pytest.mark.asyncio
    async def test_scheduling_with_timezone_aware_datetime(self):
        """Test handling of timezone-aware datetime strings (Edge case).

        Input: "2025-10-17T14:00:00+08:00 Taipei 60min"
        Expected: Correctly parse and handle timezone
        """
        # This test will be implemented when timezone support is added
        pytest.skip("Timezone support not in US1 scope - may be future enhancement")
