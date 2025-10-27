"""Agent communication protocol for multi-agent system.

Defines structured message formats for agent-to-agent communication.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent roles in the multi-agent system."""

    ORCHESTRATOR = "orchestrator"
    PARSER = "parser"
    WEATHER = "weather"
    CALENDAR = "calendar"
    DECISION = "decision"


class MessageType(str, Enum):
    """Types of messages agents can exchange."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class AgentMessage(BaseModel):
    """Base message for agent-to-agent communication."""

    message_id: str = Field(..., description="Unique message identifier")
    from_agent: AgentRole = Field(..., description="Sender agent role")
    to_agent: AgentRole = Field(..., description="Recipient agent role")
    message_type: MessageType = Field(..., description="Type of message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    content: dict[str, Any] = Field(default_factory=dict, description="Message payload")


class AgentRequest(BaseModel):
    """Request sent to an agent."""

    request_id: str = Field(..., description="Unique request identifier")
    agent_role: AgentRole = Field(..., description="Target agent role")
    action: str = Field(..., description="Action to perform (e.g., 'parse', 'check_weather')")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Action parameters"
    )
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context from previous agents"
    )


class AgentResponse(BaseModel):
    """Response from an agent."""

    request_id: str = Field(..., description="Original request ID")
    agent_role: AgentRole = Field(..., description="Responding agent role")
    success: bool = Field(..., description="Whether the action succeeded")
    result: dict[str, Any] = Field(default_factory=dict, description="Action result data")
    error: str | None = Field(default=None, description="Error message if failed")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata (e.g., timing, model used)"
    )
