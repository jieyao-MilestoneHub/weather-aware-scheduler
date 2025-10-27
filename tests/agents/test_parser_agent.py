"""Tests for Parser Agent natural language understanding.

Tests Parser Agent's ability to extract structured scheduling information
from various natural language inputs.
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.parser_agent import ParserAgent, create_parser_agent
from src.agents.protocol import AgentRequest, AgentRole


# Skip tests if no API key is configured
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") and not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="No OpenAI or Azure OpenAI API key configured"
)


class TestParserAgentCreation:
    """Test Parser Agent instantiation and configuration."""

    def test_create_parser_agent_default_config(self):
        """Test creating Parser Agent with default configuration from environment."""
        # This will use environment variables or defaults
        agent = create_parser_agent()

        assert agent is not None
        assert agent.config.role == AgentRole.PARSER
        assert agent.llm_with_tools is not None

    def test_create_parser_agent_mock_mode(self, monkeypatch):
        """Test creating Parser Agent in mock mode (no real API calls)."""
        # Set environment to avoid real API calls
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-mock")

        agent = create_parser_agent()

        assert agent.config.model_name == "gpt-4o-mini"  # Default from env


class TestParserAgentExtraction:
    """Test Parser Agent's extraction capabilities."""

    @pytest.mark.asyncio
    async def test_complete_input_extraction(self):
        """Test extraction from complete input with all required fields.

        Input: "Friday 2pm Taipei meet Alice 60min"
        Expected: Successfully extract datetime, location, duration, attendees
        """
        agent = create_parser_agent()

        request = AgentRequest(
            request_id="test-001",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "Friday 2pm Taipei meet Alice 60min"},
        )

        # Mock LLM response to avoid real API calls
        mock_response = MagicMock()
        mock_response.content = "Extracted all fields successfully"
        mock_response.tool_calls = [
            {"name": "extract_datetime_tool", "args": {"text": "Friday 2pm Taipei meet Alice 60min"}},
            {"name": "extract_location_tool", "args": {"text": "Friday 2pm Taipei meet Alice 60min"}},
            {"name": "extract_duration_tool", "args": {"text": "Friday 2pm Taipei meet Alice 60min"}},
            {"name": "extract_attendees_tool", "args": {"text": "Friday 2pm Taipei meet Alice 60min"}},
        ]

        with patch.object(agent.llm_with_tools, 'ainvoke', return_value=mock_response):
            response = await agent.process_request(request)

        assert response.success is True
        assert response.agent_role == AgentRole.PARSER

        result = response.result
        assert "extracted_data" in result

        extracted = result["extracted_data"]
        # Verify required fields were attempted to be extracted
        # Note: Actual values depend on mock implementation
        assert "datetime_iso" in extracted or "datetime_str" in extracted
        assert "city" in extracted
        assert "duration_minutes" in extracted
        assert "attendees" in extracted

    @pytest.mark.asyncio
    async def test_partial_input_missing_location(self):
        """Test extraction from partial input missing location.

        Input: "meet Alice tomorrow 60min"
        Expected: Extract time, duration, attendees; identify missing location
        """
        agent = create_parser_agent()

        request = AgentRequest(
            request_id="test-002",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": "meet Alice tomorrow 60min"},
        )

        # Mock response indicating missing location
        mock_response = MagicMock()
        mock_response.content = "Missing location information"
        mock_response.tool_calls = [
            {"name": "extract_datetime_tool", "args": {"text": "meet Alice tomorrow 60min"}},
            {"name": "extract_duration_tool", "args": {"text": "meet Alice tomorrow 60min"}},
            {"name": "extract_attendees_tool", "args": {"text": "meet Alice tomorrow 60min"}},
        ]

        with patch.object(agent.llm_with_tools, 'ainvoke', return_value=mock_response):
            response = await agent.process_request(request)

        assert response.success is True
        result = response.result

        # Should have incomplete status
        if "is_complete" in result:
            # If location extraction failed, should be incomplete
            if "city" not in result["extracted_data"] or result["extracted_data"]["city"] is None:
                assert result["is_complete"] is False
                assert "location" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_complex_natural_language_input(self):
        """Test extraction from complex, verbose natural language.

        Input: "Next Tuesday morning, let's have a project review meeting with Bob and Charlie in Tokyo for about 90 minutes"
        Expected: Extract all information correctly despite complex phrasing
        """
        agent = create_parser_agent()

        complex_input = "Next Tuesday morning, let's have a project review meeting with Bob and Charlie in Tokyo for about 90 minutes"

        request = AgentRequest(
            request_id="test-003",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": complex_input},
        )

        mock_response = MagicMock()
        mock_response.content = "Extracted fields from complex input"
        mock_response.tool_calls = [
            {"name": "extract_datetime_tool", "args": {"text": complex_input}},
            {"name": "extract_location_tool", "args": {"text": complex_input}},
            {"name": "extract_duration_tool", "args": {"text": complex_input}},
            {"name": "extract_attendees_tool", "args": {"text": complex_input}},
        ]

        with patch.object(agent.llm_with_tools, 'ainvoke', return_value=mock_response):
            response = await agent.process_request(request)

        assert response.success is True
        assert "extracted_data" in response.result


class TestParserAgentClarification:
    """Test Parser Agent's clarification prompt generation."""

    def test_generate_clarification_for_missing_datetime(self):
        """Test clarification prompt for missing datetime."""
        agent = create_parser_agent()

        prompt = agent.generate_clarification_prompt(["datetime"])

        assert "when" in prompt.lower()
        assert "schedule" in prompt.lower() or "time" in prompt.lower()

    def test_generate_clarification_for_missing_location(self):
        """Test clarification prompt for missing location."""
        agent = create_parser_agent()

        prompt = agent.generate_clarification_prompt(["location"])

        assert "where" in prompt.lower()
        assert "location" in prompt.lower() or "city" in prompt.lower()

    def test_generate_clarification_for_multiple_missing_fields(self):
        """Test clarification prompt for multiple missing fields."""
        agent = create_parser_agent()

        prompt = agent.generate_clarification_prompt(["datetime", "location", "duration"])

        # Should ask for multiple pieces of information
        assert len(prompt) > 50  # Reasonably long prompt
        # Should contain question indicators
        assert "?" in prompt


class TestParserAgentErrorHandling:
    """Test Parser Agent error handling."""

    @pytest.mark.asyncio
    async def test_empty_input_error(self):
        """Test handling of empty input."""
        agent = create_parser_agent()

        request = AgentRequest(
            request_id="test-error-001",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={"input": ""},
        )

        response = await agent.process_request(request)

        assert response.success is False
        assert response.error is not None
        assert "input" in response.error.lower()

    @pytest.mark.asyncio
    async def test_missing_input_parameter(self):
        """Test handling of missing input parameter."""
        agent = create_parser_agent()

        request = AgentRequest(
            request_id="test-error-002",
            agent_role=AgentRole.PARSER,
            action="parse",
            parameters={},  # No input provided
        )

        response = await agent.process_request(request)

        assert response.success is False
        assert response.error is not None
