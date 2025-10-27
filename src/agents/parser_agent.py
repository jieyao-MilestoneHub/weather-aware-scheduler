"""Parser Agent for natural language understanding of scheduling requests.

This agent uses LLM reasoning combined with parsing tools to extract structured
scheduling information from natural language input.
"""

import logging
import uuid
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from src.agents.base import AgentConfig, BaseSchedulerAgent, load_agent_config_from_env
from src.agents.protocol import AgentRequest, AgentResponse, AgentRole
from src.tools.parser_tools import PARSER_TOOLS

logger = logging.getLogger(__name__)

# System prompt for Parser Agent
PARSER_AGENT_SYSTEM_PROMPT = """You are a scheduling assistant specialized in understanding natural language meeting requests.

Your task is to extract the following information from user input:
1. **Date and Time**: When the meeting should occur (required)
2. **Location/City**: Where the meeting takes place (required)
3. **Duration**: How long the meeting will last (required)
4. **Attendees**: Who should attend (optional)
5. **Description**: Brief meeting description (optional)

**Available Tools**:
- extract_datetime_tool: Parse date/time from text
- extract_location_tool: Extract city/location
- extract_duration_tool: Parse meeting duration
- extract_attendees_tool: Extract attendee names
- validate_completeness_tool: Check if all required fields are present

**Instructions**:
1. Use the tools to extract information from the user's request
2. Call extract_datetime_tool, extract_location_tool, and extract_duration_tool for required fields
3. Call extract_attendees_tool if attendees are mentioned
4. Use validate_completeness_tool to check if all required information is present
5. If required information is missing, identify what's needed and return that in your response

**Output Format**:
Always return a structured response with:
- extracted_data: Dictionary with all extracted fields
- is_complete: Boolean indicating if all required fields are present
- missing_fields: List of missing required fields (if any)
- suggestions: Friendly prompt for user if information is missing

Be concise and efficient. Only ask for clarification if REQUIRED information is missing.
"""


class ParserAgent(BaseSchedulerAgent):
    """Parser Agent for natural language understanding.

    Uses LLM with tool calling to extract structured scheduling information
    from natural language input.
    """

    def __init__(self, config: AgentConfig | None = None):
        """Initialize Parser Agent.

        Args:
            config: Agent configuration. If None, loads from environment.
        """
        if config is None:
            config = load_agent_config_from_env(AgentRole.PARSER)

        super().__init__(config)

        # Bind tools to LLM
        self.llm_with_tools = self.llm_client.bind_tools(PARSER_TOOLS)

        self.logger.info(
            f"Parser Agent created with {len(PARSER_TOOLS)} tools: "
            f"{[tool.name for tool in PARSER_TOOLS]}"
        )

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process a parsing request.

        Args:
            request: AgentRequest with natural language input in parameters['input']

        Returns:
            AgentResponse with extracted scheduling information or error
        """
        try:
            user_input = request.parameters.get("input", "")
            if not user_input:
                return self.create_error_response(
                    request.request_id,
                    "No input text provided in request parameters",
                )

            self.logger.info(f"Processing parse request: '{user_input}'")

            # Create messages for LLM
            messages = [
                SystemMessage(content=PARSER_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_input),
            ]

            # Invoke LLM with tools
            response = await self.llm_with_tools.ainvoke(messages)

            self.logger.info(f"Parser agent response: {response}")

            # Check if tool calls were made
            tool_calls = getattr(response, "tool_calls", [])
            self.logger.info(f"Tool calls made: {len(tool_calls)}")

            # Execute tools and collect results
            extracted_data = {}
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                self.logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                # Find and execute the tool
                for tool in PARSER_TOOLS:
                    if tool.name == tool_name:
                        try:
                            tool_result = tool.invoke(tool_args)
                            self.logger.info(f"Tool {tool_name} result: {tool_result}")

                            # Accumulate results
                            if isinstance(tool_result, dict):
                                if (
                                    tool_name == "extract_datetime_tool"
                                    and tool_result.get("success")
                                ):
                                    extracted_data["datetime_iso"] = tool_result.get("datetime_iso")
                                    extracted_data["datetime_str"] = tool_result.get("datetime_str")
                                elif (
                                    tool_name == "extract_location_tool"
                                    and tool_result.get("success")
                                ):
                                    extracted_data["city"] = tool_result.get("city")
                                elif (
                                    tool_name == "extract_duration_tool"
                                    and tool_result.get("success")
                                ):
                                    extracted_data["duration_minutes"] = tool_result.get(
                                        "duration_minutes"
                                    )
                                elif tool_name == "extract_attendees_tool":
                                    extracted_data["attendees"] = tool_result.get("attendees", [])
                        except Exception as e:
                            self.logger.error(f"Error executing tool {tool_name}: {e}")
                        break

            # Check completeness
            is_complete = all(
                key in extracted_data and extracted_data[key] is not None
                for key in ["datetime_iso", "city", "duration_minutes"]
            )

            missing_fields = []
            if "datetime_iso" not in extracted_data or extracted_data["datetime_iso"] is None:
                missing_fields.append("datetime")
            if "city" not in extracted_data or extracted_data["city"] is None:
                missing_fields.append("location")
            if (
                "duration_minutes" not in extracted_data
                or extracted_data["duration_minutes"] is None
            ):
                missing_fields.append("duration")

            # Get agent's text response
            agent_output = response.content if hasattr(response, "content") else str(response)

            return self.create_success_response(
                request.request_id,
                result={
                    "extracted_data": extracted_data,
                    "is_complete": is_complete,
                    "missing_fields": missing_fields,
                    "agent_output": agent_output,
                },
                metadata={
                    "tool_calls": len(tool_calls),
                    "model": self.config.model_name,
                },
            )

        except Exception as e:
            self.logger.exception(f"Error processing parse request: {e}")
            return self.create_error_response(
                request.request_id,
                f"Parser agent failed: {str(e)}",
            )

    def generate_clarification_prompt(self, missing_fields: list[str]) -> str:
        """Generate a friendly prompt asking for missing information.

        Args:
            missing_fields: List of missing field names

        Returns:
            User-friendly prompt string
        """
        prompts = {
            "datetime": "When would you like to schedule this meeting? (e.g., 'Friday 2pm', 'tomorrow afternoon', 'next Monday at 10am')",
            "location": "Where should this meeting take place? Please specify a city or location.",
            "duration": "How long should the meeting last? (e.g., '60 minutes', '1 hour', '30 min')",
        }

        if not missing_fields:
            return ""

        if len(missing_fields) == 1:
            return prompts.get(missing_fields[0], f"Please provide: {missing_fields[0]}")

        # Multiple missing fields
        questions = [prompts.get(field, field) for field in missing_fields]
        return "I need a bit more information:\n" + "\n".join(
            f"{i+1}. {q}" for i, q in enumerate(questions)
        )


# Factory function for easy instantiation
def create_parser_agent(config: AgentConfig | None = None) -> ParserAgent:
    """Create a Parser Agent instance.

    Args:
        config: Optional agent configuration. If None, loads from environment.

    Returns:
        Configured ParserAgent instance
    """
    return ParserAgent(config)
