"""Core entity models for scheduling operations."""

from datetime import datetime as dt_type
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RiskCategory(str, Enum):
    """Weather risk categorization."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class Slot(BaseModel):
    """Extracted structured data from natural language input.

    Represents a scheduling request with all necessary details.
    """
    city: str = Field(..., min_length=1, description="Location city name")
    datetime: dt_type = Field(..., description="Scheduled datetime")
    duration: int = Field(..., ge=5, le=480, description="Duration in minutes (5-480)")
    attendees: list[str] = Field(default_factory=list, description="List of attendee names")
    description: str | None = Field(None, description="Optional event description")

    @field_validator("datetime")
    @classmethod
    def datetime_must_be_future(cls, v: dt_type) -> dt_type:
        """Validate that datetime is in the future."""
        now = dt_type.now(v.tzinfo)
        if v <= now:
            raise ValueError("Datetime must be in the future")
        return v

    @field_validator("city")
    @classmethod
    def city_must_not_be_empty(cls, v: str) -> str:
        """Validate that city is not empty or whitespace."""
        if not v.strip():
            raise ValueError("City must not be empty")
        return v.strip()


class WeatherCondition(BaseModel):
    """Weather forecast information for a specific time and location."""
    prob_rain: int = Field(..., ge=0, le=100, description="Rain probability (0-100%)")
    risk_category: RiskCategory = Field(..., description="Risk categorization")
    description: str = Field(..., description="Human-readable weather description")

    @field_validator("risk_category", mode="before")
    @classmethod
    def categorize_risk(cls, v: Any, info: Any) -> RiskCategory:
        """Auto-categorize risk based on prob_rain if not provided."""
        if isinstance(v, RiskCategory):
            return v

        # Get prob_rain from values being validated
        prob_rain = info.data.get("prob_rain", 0)

        if prob_rain >= 60:
            return RiskCategory.HIGH
        elif prob_rain >= 30:
            return RiskCategory.MODERATE
        else:
            return RiskCategory.LOW


class CalendarEvent(BaseModel):
    """Confirmed scheduled event."""
    event_id: str = Field(..., description="Unique event identifier")
    city: str = Field(..., description="Event location")
    datetime: dt_type = Field(..., description="Event datetime")
    duration: int = Field(..., ge=5, le=480, description="Duration in minutes")
    attendees: list[str] = Field(default_factory=list, description="Attendee names")
    reason: str = Field(..., description="Reason for scheduling decision")
    notes: str | None = Field(None, description="Additional notes or warnings")
    status: str = Field(default="confirmed", description="Event status")


class Conflict(BaseModel):
    """Represents a scheduling conflict."""
    conflicting_event_id: str | None = Field(None, description="ID of conflicting event")
    conflicting_time: dt_type = Field(..., description="Time of conflict")
    duration: int = Field(..., description="Duration of conflicting event")
    next_available: dt_type | None = Field(None, description="Next available time slot")
    candidates: list[dt_type] = Field(
        default_factory=list,
        description="Top 3 alternative time slots",
        max_length=3
    )
