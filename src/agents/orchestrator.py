"""Orchestrator for coordinating multi-agent workflows.

The Orchestrator manages the interaction between specialized agents
(Parser, Calendar, Weather, Decision) to complete scheduling tasks.

For US1 (Simple Schedule Creation), the workflow is:
1. Parser Agent extracts scheduling information from natural language
2. Calendar Agent checks availability and creates event
3. Return result to user
"""

import logging
from datetime import datetime
from typing import Any

from src.agents.calendar_agent import create_calendar_agent
from src.agents.parser_agent import create_parser_agent
from src.agents.protocol import AgentRequest, AgentResponse, AgentRole
from src.models.entities import CalendarEvent

logger = logging.getLogger(__name__)


class SimpleSchedulerOrchestrator:
    """Simple orchestrator for US1 - Basic schedule creation without weather/conflict logic.

    This orchestrator implements the MVP workflow:
    1. Parse natural language input
    2. Check calendar availability
    3. Create event or suggest alternatives

    Future: Will be extended for US2 (weather-aware), US3 (conflict resolution)
    """

    def __init__(self):
        """Initialize orchestrator with Parser and Calendar agents."""
        self.parser_agent = create_parser_agent()
        self.calendar_agent = create_calendar_agent()

        logger.info("SimpleSchedulerOrchestrator initialized with Parser and Calendar agents")

    async def schedule(self, user_input: str) -> dict[str, Any]:
        """Schedule an event from natural language input.

        Args:
            user_input: Natural language scheduling request
                Example: "Friday 10am Taipei meet Alice 60min"

        Returns:
            Dictionary with scheduling result:
            {
                "success": bool,
                "event": CalendarEvent dict (if success),
                "message": str,
                "clarification_needed": list[str] (if incomplete),
                "error": str (if failed)
            }
        """
        try:
            logger.info(f"Processing scheduling request: {user_input}")

            # Step 1: Parse natural language input
            parse_result = await self._parse_input(user_input)

            if not parse_result["success"]:
                # Parsing failed
                return {
                    "success": False,
                    "event": None,
                    "message": "Failed to parse input",
                    "error": parse_result.get("error", "Unknown parse error")
                }

            # Check if parsing is complete
            is_complete = parse_result.get("is_complete", False)
            extracted_data = parse_result.get("extracted_data", {})

            if not is_complete:
                # Missing required fields - return clarification request
                missing_fields = parse_result.get("missing_fields", [])
                suggestions = parse_result.get("suggestions", "Please provide missing information")

                return {
                    "success": False,
                    "event": None,
                    "message": suggestions,
                    "clarification_needed": missing_fields,
                    "error": None
                }

            # Step 2: Check calendar availability
            datetime_iso = extracted_data.get("datetime_iso")
            duration_min = extracted_data.get("duration_minutes", 60)

            if not datetime_iso:
                return {
                    "success": False,
                    "event": None,
                    "message": "Could not determine event time",
                    "error": "Missing datetime_iso in extracted data"
                }

            availability_result = await self._check_availability(datetime_iso, duration_min)

            if not availability_result["success"]:
                return {
                    "success": False,
                    "event": None,
                    "message": "Failed to check availability",
                    "error": availability_result.get("error", "Unknown availability error")
                }

            # Step 3: Handle availability check result
            is_available = availability_result.get("is_available", False)

            if not is_available:
                # Requested time is busy - find alternative
                logger.info(f"Requested time {datetime_iso} is busy, finding alternative")

                free_slot_result = await self._find_free_slot(datetime_iso, duration_min)

                if not free_slot_result["success"]:
                    return {
                        "success": False,
                        "event": None,
                        "message": "No free slots available",
                        "error": free_slot_result.get("error", "Could not find free slot")
                    }

                # Use the free slot found
                free_slot = free_slot_result.get("free_slot", {})
                datetime_iso = free_slot.get("datetime_iso", datetime_iso)

                logger.info(f"Found free slot at {datetime_iso}")

            # Step 4: Create calendar event
            city = extracted_data.get("city", "Unknown")
            attendees = extracted_data.get("attendees", [])
            description = extracted_data.get("description", "")

            event_result = await self._create_event(
                city=city,
                datetime_iso=datetime_iso,
                duration_min=duration_min,
                attendees=attendees,
                notes=description
            )

            if not event_result["success"]:
                return {
                    "success": False,
                    "event": None,
                    "message": "Failed to create event",
                    "error": event_result.get("error", "Unknown create event error")
                }

            # Success!
            event = event_result.get("event", {})

            return {
                "success": True,
                "event": event,
                "message": f"Event created successfully at {event.get('datetime_iso')} in {event.get('city')}",
                "error": None
            }

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            return {
                "success": False,
                "event": None,
                "message": "Internal orchestrator error",
                "error": str(e)
            }

    async def _parse_input(self, user_input: str) -> dict[str, Any]:
        """Parse natural language input using Parser Agent.

        Args:
            user_input: Natural language text

        Returns:
            Dictionary with parse results
        """
        request = AgentRequest(
            request_id=f"parse-{datetime.now().timestamp()}",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": user_input}
        )

        response: AgentResponse = await self.parser_agent.process_request(request)

        return {
            "success": response.success,
            "is_complete": response.result.get("is_complete", False) if response.success else False,
            "extracted_data": response.result.get("extracted_data", {}) if response.success else {},
            "missing_fields": response.result.get("missing_fields", []) if response.success else [],
            "suggestions": response.result.get("suggestions", "") if response.success else "",
            "error": response.error
        }

    async def _check_availability(self, datetime_iso: str, duration_min: int) -> dict[str, Any]:
        """Check calendar availability using Calendar Agent.

        Args:
            datetime_iso: ISO format datetime string
            duration_min: Duration in minutes

        Returns:
            Dictionary with availability status
        """
        request = AgentRequest(
            request_id=f"check-avail-{datetime.now().timestamp()}",
            agent_role=AgentRole.CALENDAR,
            action="check_availability",
            parameters={
                "datetime_iso": datetime_iso,
                "duration_min": duration_min
            }
        )

        response: AgentResponse = await self.calendar_agent.process_request(request)

        return {
            "success": response.success,
            "is_available": response.result.get("is_available", False) if response.success else False,
            "reason": response.result.get("reason") if response.success else None,
            "error": response.error
        }

    async def _find_free_slot(self, datetime_iso: str, duration_min: int) -> dict[str, Any]:
        """Find free slot using Calendar Agent.

        Args:
            datetime_iso: Preferred datetime (ISO format)
            duration_min: Required duration in minutes

        Returns:
            Dictionary with free slot information
        """
        request = AgentRequest(
            request_id=f"find-free-{datetime.now().timestamp()}",
            agent_role=AgentRole.CALENDAR,
            action="find_free_slot",
            parameters={
                "datetime_iso": datetime_iso,
                "duration_min": duration_min
            }
        )

        response: AgentResponse = await self.calendar_agent.process_request(request)

        return {
            "success": response.result.get("success", False) if response.success else False,
            "free_slot": response.result.get("free_slot") if response.success else None,
            "alternatives": response.result.get("alternatives", []) if response.success else [],
            "error": response.error
        }

    async def _create_event(
        self,
        city: str,
        datetime_iso: str,
        duration_min: int,
        attendees: list[str],
        notes: str
    ) -> dict[str, Any]:
        """Create calendar event using Calendar Agent.

        Args:
            city: Event location
            datetime_iso: Event datetime (ISO format)
            duration_min: Event duration in minutes
            attendees: List of attendee names
            notes: Event notes/description

        Returns:
            Dictionary with created event details
        """
        request = AgentRequest(
            request_id=f"create-event-{datetime.now().timestamp()}",
            agent_role=AgentRole.CALENDAR,
            action="create_event",
            parameters={
                "city": city,
                "datetime_iso": datetime_iso,
                "duration_min": duration_min,
                "attendees": attendees,
                "notes": notes
            }
        )

        response: AgentResponse = await self.calendar_agent.process_request(request)

        return {
            "success": response.result.get("success", False) if response.success else False,
            "event": response.result.get("event") if response.success else None,
            "error": response.error
        }


def create_orchestrator() -> SimpleSchedulerOrchestrator:
    """Create simple scheduler orchestrator.

    Returns:
        Initialized SimpleSchedulerOrchestrator
    """
    return SimpleSchedulerOrchestrator()
