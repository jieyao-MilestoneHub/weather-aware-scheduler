"""LangChain tool wrappers for Calendar Agent.

Wraps existing calendar tool functions as tools that can be used by LLM agents.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.mock_calendar import MockCalendarTool
from src.models.entities import Slot

logger = logging.getLogger(__name__)


# Pydantic schemas for tool inputs
class CheckAvailabilityInput(BaseModel):
    """Input for check availability tool."""

    datetime_iso: str = Field(..., description="ISO format datetime string (e.g., '2025-10-27T14:00:00')")
    duration_min: int = Field(..., description="Duration in minutes")


class FindFreeSlotInput(BaseModel):
    """Input for find free slot tool."""

    datetime_iso: str = Field(..., description="ISO format datetime string for preferred time")
    duration_min: int = Field(..., description="Duration in minutes")


class CreateEventInput(BaseModel):
    """Input for create event tool."""

    city: str = Field(..., description="City/location for the event")
    datetime_iso: str = Field(..., description="ISO format datetime string")
    duration_min: int = Field(..., description="Duration in minutes")
    attendees: list[str] = Field(default_factory=list, description="List of attendee names")
    notes: str = Field(default="", description="Additional notes or description")


# Tool definitions
@tool(args_schema=CheckAvailabilityInput)
def check_availability_tool(datetime_iso: str, duration_min: int) -> dict[str, Any]:
    """Check if a time slot is available in the calendar.

    Args:
        datetime_iso: ISO format datetime string
        duration_min: Duration in minutes

    Returns:
        Dictionary with:
        - is_available: Boolean indicating availability
        - datetime_iso: Queried datetime
        - duration_min: Queried duration
        - reason: Optional reason if not available
    """
    try:
        dt = datetime.fromisoformat(datetime_iso)
        calendar_tool = MockCalendarTool()

        # Check if slot is available using MockCalendarTool logic
        # MockCalendarTool.is_available() checks against busy times
        # Busy times: Friday 3pm (15:00)
        is_friday_3pm = dt.weekday() == 4 and dt.hour == 15

        is_available = not is_friday_3pm

        logger.info(
            f"Checked availability for {datetime_iso} ({duration_min}min): "
            f"{'available' if is_available else 'busy'}"
        )

        return {
            "is_available": is_available,
            "datetime_iso": datetime_iso,
            "duration_min": duration_min,
            "reason": "Time slot is busy" if not is_available else None,
        }

    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return {
            "is_available": False,
            "datetime_iso": datetime_iso,
            "duration_min": duration_min,
            "error": str(e),
        }


@tool(args_schema=FindFreeSlotInput)
def find_free_slot_tool(datetime_iso: str, duration_min: int) -> dict[str, Any]:
    """Find next available free time slot.

    If the requested time is busy, finds the next available slot that can
    accommodate the requested duration.

    Args:
        datetime_iso: Preferred datetime (ISO format)
        duration_min: Required duration in minutes

    Returns:
        Dictionary with:
        - success: Boolean indicating if free slot found
        - free_slot: Dictionary with datetime_iso and duration_min
        - alternatives: List of alternative slots
    """
    try:
        dt = datetime.fromisoformat(datetime_iso)
        calendar_tool = MockCalendarTool()

        # Use MockCalendarTool's find_free_slot method (returns dict with status/next_available/candidates)
        result = calendar_tool.find_free_slot(dt, duration_min)

        if result["status"] != "available" or not result.get("next_available"):
            # No free slot found in search window
            logger.warning(f"No free slot found starting from {datetime_iso}")
            return {
                "success": False,
                "free_slot": None,
                "alternatives": [],
                "error": "No free slot found in search window"
            }

        # Found free slot
        free_slot_dt = result["next_available"]
        logger.info(f"Found free slot: {free_slot_dt.isoformat()}")

        # Generate additional alternatives (next 2 slots after the found one)
        alternatives = []
        if free_slot_dt != dt:
            # If we found a different slot, generate more alternatives
            alt1 = free_slot_dt + timedelta(minutes=30)
            alt2 = free_slot_dt + timedelta(minutes=60)
            alternatives = [
                {"datetime_iso": alt1.isoformat(), "duration_min": duration_min},
                {"datetime_iso": alt2.isoformat(), "duration_min": duration_min},
            ]

        return {
            "success": True,
            "free_slot": {
                "datetime_iso": free_slot_dt.isoformat(),
                "duration_min": duration_min,
            },
            "alternatives": alternatives,
        }

    except Exception as e:
        logger.error(f"Error finding free slot: {e}")
        return {
            "success": False,
            "free_slot": None,
            "error": str(e),
        }


@tool(args_schema=CreateEventInput)
def create_event_tool(
    city: str, datetime_iso: str, duration_min: int, attendees: list[str], notes: str
) -> dict[str, Any]:
    """Create a calendar event.

    Args:
        city: Event location (city)
        datetime_iso: Event datetime (ISO format)
        duration_min: Event duration in minutes
        attendees: List of attendee names
        notes: Event notes/description

    Returns:
        Dictionary with:
        - success: Boolean indicating if event created
        - event: Created event details
        - error: Error message if failed
    """
    try:
        dt = datetime.fromisoformat(datetime_iso)
        calendar_tool = MockCalendarTool()

        # Create event using MockCalendarTool with keyword arguments
        event = calendar_tool.create_event(
            city=city,
            dt=dt,
            duration_min=duration_min,
            attendees=attendees,
            notes=notes or "Scheduled meeting"
        )

        logger.info(f"Created event: {event.event_id} at {datetime_iso} in {city}")

        return {
            "success": True,
            "event": {
                "id": event.event_id,
                "event_id": event.event_id,
                "city": city,
                "datetime_iso": datetime_iso,
                "duration_min": duration_min,
                "attendees": attendees,
                "notes": notes,
                "status": event.status,
            },
            "error": None,
        }

    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return {
            "success": False,
            "event": None,
            "error": str(e),
        }


# Export all calendar tools as a list for easy binding to agents
CALENDAR_TOOLS = [
    check_availability_tool,
    find_free_slot_tool,
    create_event_tool,
]
