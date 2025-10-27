"""Multi-Agent system based on Microsoft Agent Framework."""

from src.agents.base import BaseSchedulerAgent
from src.agents.calendar_agent import CalendarAgent, create_calendar_agent
from src.agents.orchestrator import SimpleSchedulerOrchestrator, create_orchestrator
from src.agents.parser_agent import ParserAgent, create_parser_agent
from src.agents.protocol import AgentMessage, AgentRequest, AgentResponse

__all__ = [
    "BaseSchedulerAgent",
    "ParserAgent",
    "create_parser_agent",
    "CalendarAgent",
    "create_calendar_agent",
    "SimpleSchedulerOrchestrator",
    "create_orchestrator",
    "AgentMessage",
    "AgentRequest",
    "AgentResponse",
]
