"""Output models for scheduling decisions and summaries."""

from datetime import datetime as dt_type
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Type of scheduling action to take."""
    CREATE = "create"
    ADJUST_TIME = "adjust_time"
    ADJUST_PLACE = "adjust_place"
    PROPOSE_CANDIDATES = "propose_candidates"


class EventStatus(str, Enum):
    """Status of the scheduling request."""
    CONFIRMED = "confirmed"
    ADJUSTED = "adjusted"
    CONFLICT = "conflict"
    ERROR = "error"


class PolicyDecision(BaseModel):
    """Decision made by the policy/adjustment logic."""
    action: ActionType = Field(..., description="Action to take")
    reason: str = Field(..., description="Explanation for the decision")
    notes: str | None = Field(None, description="Additional notes or warnings")
    adjustments: dict[str, Any] = Field(
        default_factory=dict,
        description="Adjustment details (time shifts, indoor hints, candidates)"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class EventSummary(BaseModel):
    """Final summary of the scheduling operation."""
    status: EventStatus = Field(..., description="Overall status")
    summary_text: str = Field(..., description="Human-readable summary")
    reason: str = Field(..., description="Reason for the outcome")
    notes: str | None = Field(None, description="Additional notes or warnings")
    alternatives: list[dt_type] | None = Field(
        None,
        description="Alternative time slots (if conflict)",
        max_length=3
    )
    event_id: str | None = Field(None, description="Created event ID (if successful)")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
