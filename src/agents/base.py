"""Base agent class for all scheduler agents.

Provides common functionality for agent initialization, LLM client setup,
and communication protocols.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

from agent_framework import BaseAgent, ChatAgent
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import BaseModel

from src.agents.protocol import AgentRequest, AgentResponse, AgentRole

logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration for an agent."""

    role: AgentRole
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout: float = 30.0
    use_azure: bool = False


class BaseSchedulerAgent(ABC):
    """Base class for all scheduler agents.

    Provides:
    - LLM client initialization (OpenAI or Azure OpenAI)
    - Agent lifecycle management
    - Request/response handling
    - Error handling and logging
    """

    def __init__(self, config: AgentConfig):
        """Initialize the base agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.role.value}")
        self.llm_client = self._initialize_llm_client()
        self.agent: BaseAgent | None = None

    def _initialize_llm_client(self) -> ChatOpenAI | AzureChatOpenAI:
        """Initialize LLM client based on environment configuration.

        Returns:
            LangChain chat model instance

        Raises:
            ValueError: If required environment variables are missing
        """
        if self.config.use_azure or os.getenv("AZURE_OPENAI_API_KEY"):
            # Use Azure OpenAI
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", self.config.model_name)

            if not api_key or not endpoint:
                raise ValueError(
                    "Azure OpenAI requires AZURE_OPENAI_API_KEY and "
                    "AZURE_OPENAI_ENDPOINT environment variables"
                )

            self.logger.info(
                f"Initializing Azure OpenAI client for {self.config.role.value} "
                f"with deployment {deployment}"
            )

            return AzureChatOpenAI(
                azure_deployment=deployment,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )
        else:
            # Use OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI requires OPENAI_API_KEY environment variable. "
                    "Set OPENAI_API_KEY or configure Azure OpenAI instead."
                )

            self.logger.info(
                f"Initializing OpenAI client for {self.config.role.value} "
                f"with model {self.config.model_name}"
            )

            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout,
            )

    @abstractmethod
    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """Process an agent request and return a response.

        This method must be implemented by each specific agent.

        Args:
            request: The request to process

        Returns:
            AgentResponse with the result or error
        """
        pass

    def create_success_response(
        self, request_id: str, result: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Create a successful response.

        Args:
            request_id: Original request ID
            result: Result data
            metadata: Optional metadata

        Returns:
            AgentResponse indicating success
        """
        return AgentResponse(
            request_id=request_id,
            agent_role=self.config.role,
            success=True,
            result=result,
            metadata=metadata or {},
        )

    def create_error_response(
        self, request_id: str, error: str, metadata: dict[str, Any] | None = None
    ) -> AgentResponse:
        """Create an error response.

        Args:
            request_id: Original request ID
            error: Error message
            metadata: Optional metadata

        Returns:
            AgentResponse indicating failure
        """
        self.logger.error(f"Error in {self.config.role.value}: {error}")
        return AgentResponse(
            request_id=request_id,
            agent_role=self.config.role,
            success=False,
            result={},
            error=error,
            metadata=metadata or {},
        )


def load_agent_config_from_env(role: AgentRole) -> AgentConfig:
    """Load agent configuration from environment variables.

    Args:
        role: The agent role to configure

    Returns:
        AgentConfig with settings from environment or defaults
    """
    # Get role-specific environment variable names
    role_upper = role.value.upper()
    model_env = f"{role_upper}_AGENT_MODEL"
    temp_env = f"{role_upper}_AGENT_TEMPERATURE"

    # Load from environment with fallbacks
    model_name = os.getenv(model_env, "gpt-4o-mini")
    temperature = float(os.getenv(temp_env, "0.0"))

    # Determine if using Azure
    use_azure = bool(os.getenv("AZURE_OPENAI_API_KEY"))

    return AgentConfig(
        role=role,
        model_name=model_name,
        temperature=temperature,
        use_azure=use_azure,
    )
