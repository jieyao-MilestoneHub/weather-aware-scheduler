"""Calendar Agent for calendar operations and event scheduling.

This agent uses LLM reasoning combined with calendar tools to:
- Check availability of time slots
- Find free slots when conflicts exist
- Create calendar events

The agent acts as an intelligent wrapper around calendar operations,
using the LLM to interpret requests and call appropriate calendar tools.
"""

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import AgentConfig, BaseSchedulerAgent, load_agent_config_from_env
from src.agents.protocol import AgentRequest, AgentResponse, AgentRole
from src.tools.calendar_tools import CALENDAR_TOOLS

logger = logging.getLogger(__name__)

# System prompt for Calendar Agent
CALENDAR_AGENT_SYSTEM_PROMPT = """You are a calendar management assistant specialized in scheduling and availability checking.

Your task is to help with calendar operations:
1. **Check Availability**: Determine if a time slot is free or busy
2. **Find Free Slots**: Find alternative times when requested slot is busy
3. **Create Events**: Schedule calendar events with all necessary details

**Available Tools**:
- check_availability_tool: Check if a specific time slot is available
- find_free_slot_tool: Find the next available free slot
- create_event_tool: Create a calendar event

**Instructions**:
1. Use the appropriate tool based on the requested action
2. For "check_availability" action: Use check_availability_tool
3. For "find_free_slot" action: Use find_free_slot_tool
4. For "create_event" action: Use create_event_tool
5. Always return structured results with success status

**Output Format**:
Return the tool result directly. Each tool returns:
- check_availability_tool: {is_available, datetime_iso, duration_min, reason}
- find_free_slot_tool: {success, free_slot, alternatives}
- create_event_tool: {success, event, error}

Be efficient and precise. Always use the tools to perform calendar operations.
"""


class CalendarAgent(BaseSchedulerAgent):
    """Calendar Agent for calendar operations.

    Uses LLM with tool calling to perform intelligent calendar management
    including availability checks, slot finding, and event creation.
    """

    def __init__(self, config: AgentConfig | None = None):
        """Initialize Calendar Agent.

        Args:
            config: Agent configuration. If None, loads from environment.
        """
        if config is None:
            config = load_agent_config_from_env(AgentRole.CALENDAR)

        super().__init__(config)

        # Bind tools to LLM
        self.llm_with_tools = self.llm_client.bind_tools(CALENDAR_TOOLS)

        self.logger.info(
            f"Calendar Agent created with {len(CALENDAR_TOOLS)} tools: "
            f"{[tool.name for tool in CALENDAR_TOOLS]}"
        )

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process calendar operation request.

        Args:
            request: Agent request with action and parameters

        Returns:
            AgentResponse with calendar operation result

        Supported Actions:
            - check_availability: Check if time slot is available
            - find_free_slot: Find next available free slot
            - create_event: Create calendar event
        """
        try:
            # Validate request
            if request.agent_role != AgentRole.CALENDAR:
                return self._error_response(
                    request,
                    f"Invalid agent role: {request.agent_role}, expected CALENDAR"
                )

            # Extract action and parameters
            action = request.action
            params = request.parameters

            # Route to appropriate handler based on action
            if action == "check_availability":
                result = await self._check_availability(params)
            elif action == "find_free_slot":
                result = await self._find_free_slot(params)
            elif action == "create_event":
                result = await self._create_event(params)
            else:
                return self._error_response(
                    request,
                    f"Unknown action: {action}. Supported: check_availability, find_free_slot, create_event"
                )

            # Return success response
            return AgentResponse(
                request_id=request.request_id,
                agent_role=AgentRole.CALENDAR,
                success=True,
                result=result,
                error=None
            )

        except Exception as e:
            self.logger.error(f"Error processing calendar request: {e}", exc_info=True)
            return self._error_response(request, str(e))

    async def _check_availability(self, params: dict[str, Any]) -> dict[str, Any]:
        """Check if a time slot is available.

        Args:
            params: Dictionary with datetime_iso and duration_min

        Returns:
            Dictionary with availability status
        """
        # Validate required parameters
        if "datetime_iso" not in params:
            raise ValueError("Missing required parameter: datetime_iso")
        if "duration_min" not in params:
            raise ValueError("Missing required parameter: duration_min")

        datetime_iso = params["datetime_iso"]
        duration_min = params["duration_min"]

        # Build prompt for LLM
        user_message = (
            f"Check if the time slot at {datetime_iso} for {duration_min} minutes is available. "
            f"Use the check_availability_tool."
        )

        # Call LLM with tools
        messages = [
            SystemMessage(content=CALENDAR_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = await self.llm_with_tools.ainvoke(messages)

        # Execute tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "check_availability_tool":
                    # Find and invoke the tool
                    for tool in CALENDAR_TOOLS:
                        if tool.name == "check_availability_tool":
                            result = tool.invoke(tool_call["args"])
                            return result

        # If no tool call was made, return error
        raise RuntimeError("LLM did not call check_availability_tool")

    async def _find_free_slot(self, params: dict[str, Any]) -> dict[str, Any]:
        """Find next available free slot.

        Args:
            params: Dictionary with datetime_iso and duration_min

        Returns:
            Dictionary with free slot information
        """
        # Validate required parameters
        if "datetime_iso" not in params:
            raise ValueError("Missing required parameter: datetime_iso")
        if "duration_min" not in params:
            raise ValueError("Missing required parameter: duration_min")

        datetime_iso = params["datetime_iso"]
        duration_min = params["duration_min"]

        # Build prompt for LLM
        user_message = (
            f"Find the next available free slot starting from {datetime_iso} "
            f"for {duration_min} minutes. Use the find_free_slot_tool."
        )

        # Call LLM with tools
        messages = [
            SystemMessage(content=CALENDAR_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = await self.llm_with_tools.ainvoke(messages)

        # Execute tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "find_free_slot_tool":
                    # Find and invoke the tool
                    for tool in CALENDAR_TOOLS:
                        if tool.name == "find_free_slot_tool":
                            result = tool.invoke(tool_call["args"])
                            return result

        # If no tool call was made, return error
        raise RuntimeError("LLM did not call find_free_slot_tool")

    async def _create_event(self, params: dict[str, Any]) -> dict[str, Any]:
        """Create a calendar event.

        Args:
            params: Dictionary with city, datetime_iso, duration_min, attendees, notes

        Returns:
            Dictionary with created event details
        """
        # Validate required parameters
        required = ["city", "datetime_iso", "duration_min"]
        for param in required:
            if param not in params:
                raise ValueError(f"Missing required parameter: {param}")

        # Extract parameters (with defaults for optional fields)
        city = params["city"]
        datetime_iso = params["datetime_iso"]
        duration_min = params["duration_min"]
        attendees = params.get("attendees", [])
        notes = params.get("notes", "")

        # Build prompt for LLM
        user_message = (
            f"Create a calendar event in {city} at {datetime_iso} "
            f"for {duration_min} minutes. "
            f"Attendees: {attendees if attendees else 'none'}. "
            f"Notes: {notes if notes else 'none'}. "
            f"Use the create_event_tool."
        )

        # Call LLM with tools
        messages = [
            SystemMessage(content=CALENDAR_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]

        response = await self.llm_with_tools.ainvoke(messages)

        # Execute tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "create_event_tool":
                    # Find and invoke the tool
                    for tool in CALENDAR_TOOLS:
                        if tool.name == "create_event_tool":
                            result = tool.invoke(tool_call["args"])
                            return result

        # If no tool call was made, return error
        raise RuntimeError("LLM did not call create_event_tool")

    def _error_response(self, request: AgentRequest, error_message: str) -> AgentResponse:
        """Create error response.

        Args:
            request: Original request
            error_message: Error message

        Returns:
            AgentResponse with error
        """
        return AgentResponse(
            request_id=request.request_id,
            agent_role=AgentRole.CALENDAR,
            success=False,
            result={},
            error=error_message
        )


def create_calendar_agent(config: AgentConfig | None = None) -> CalendarAgent:
    """Create Calendar Agent with configuration.

    Args:
        config: Optional agent configuration. If None, loads from environment.

    Returns:
        Initialized Calendar Agent
    """
    return CalendarAgent(config=config)
