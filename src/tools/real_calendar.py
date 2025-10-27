"""Real calendar tool using OpenAI API for intelligent scheduling.

This tool uses OpenAI's LLM to simulate calendar operations and conflict detection.
In production, this should be replaced with real calendar APIs (e.g., Google Calendar,
Microsoft Graph API, CalDAV).
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.models.entities import CalendarEvent, Slot
from src.tools.base import CalendarTool, CalendarServiceError


class ConflictCheckOutput(BaseModel):
    """Output schema for conflict checking."""
    has_conflict: bool = Field(description="Whether there is a calendar conflict")
    conflict_reason: Optional[str] = Field(
        default=None, description="Reason for conflict if any"
    )
    suggested_times: list[str] = Field(
        default_factory=list,
        description="ISO format datetime strings for alternative times if conflict exists",
    )


class RealCalendarTool(CalendarTool):
    """Real calendar tool using OpenAI API for intelligent scheduling.

    Note: This uses LLM-based simulation as a placeholder. For production,
    integrate with real calendar APIs like Google Calendar or Microsoft Graph.
    """

    def __init__(self):
        """Initialize the real calendar tool with OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "sk-...":
            raise ValueError(
                "OPENAI_API_KEY not set in environment. "
                "Please set it in .env file or export it. "
                "Get your key from: https://platform.openai.com/api-keys"
            )

        # Use Azure OpenAI if configured
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_endpoint:
            from langchain_openai import AzureChatOpenAI
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                temperature=0.1,
            )
        else:
            # Use standard OpenAI
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,
                api_key=api_key,
            )

        # Create structured output LLM
        self.structured_llm = self.llm.with_structured_output(ConflictCheckOutput)

    def check_slot_availability(self, dt: datetime, duration_min: int) -> dict:
        """Check if a time slot is available using LLM simulation.

        Args:
            dt: Target datetime
            duration_min: Duration in minutes

        Returns:
            Dictionary with status and conflict info

        Raises:
            CalendarServiceError: If API call fails
        """
        try:
            end_time = dt + timedelta(minutes=duration_min)

            # Format prompt for conflict checking
            prompt = f"""You are a calendar conflict detection assistant. Check if this time slot is likely available:

Requested Time: {dt.strftime('%A, %B %d, %Y at %I:%M %p')}
Duration: {duration_min} minutes
End Time: {end_time.strftime('%I:%M %p')}

Consider typical business hours and common meeting times:
- Avoid lunch hours (12-1 PM) on weekdays
- Prefer morning/afternoon slots on weekdays
- Weekends are usually free unless specified

Determine if there's likely a conflict and suggest 3 alternative times if needed.
Make alternatives realistic (within same day or next business day, similar time slots)."""

            # Call LLM with structured output
            result = self.structured_llm.invoke(prompt)

            if result.has_conflict:
                # Parse suggested times
                candidates = []
                for time_str in result.suggested_times[:3]:
                    try:
                        suggested_dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
                        candidates.append(suggested_dt)
                    except:
                        # If parsing fails, generate alternatives manually
                        candidates.append(dt + timedelta(minutes=30 * (len(candidates) + 1)))

                return {
                    "status": "conflict",
                    "conflict_details": {
                        "start": dt,
                        "end": end_time,
                        "summary": result.conflict_reason or "Calendar conflict detected",
                    },
                    "candidates": candidates[:3],
                }
            else:
                return {
                    "status": "available",
                    "conflict_details": None,
                    "candidates": [],
                }

        except Exception as e:
            raise CalendarServiceError(f"Calendar API call failed: {str(e)}")

    def create_event(
        self, city: str, dt: datetime, duration_min: int, attendees: list[str], notes: Optional[str]
    ) -> CalendarEvent:
        """Create a calendar event.

        Args:
            city: Event location
            dt: Event datetime
            duration_min: Duration in minutes
            attendees: List of attendee names
            notes: Event notes

        Returns:
            CalendarEvent object with created event details

        Raises:
            CalendarServiceError: If API call fails
        """
        try:
            event_id = f"real-event-{uuid.uuid4().hex[:8]}"

            return CalendarEvent(
                event_id=event_id,
                city=city,
                datetime=dt,
                duration=duration_min,
                attendees=attendees,
                notes=notes or f"Meeting in {city}",
                status="confirmed",
                reason="Event created successfully using AI scheduling",
            )

        except Exception as e:
            raise CalendarServiceError(f"Failed to create event: {str(e)}")

    def check_conflicts(self, dt: datetime, duration_min: int) -> list[dict]:
        """Check for conflicts (alternative interface).

        Args:
            dt: Target datetime
            duration_min: Duration in minutes

        Returns:
            List of conflicting events (empty if no conflicts)
        """
        result = self.check_slot_availability(dt, duration_min)
        if result["status"] == "conflict" and result["conflict_details"]:
            return [result["conflict_details"]]
        return []

    def find_free_slot(
        self, start_search: datetime, duration_min: int, search_window_hours: int = 8
    ) -> dict:
        """Find next available free slot.

        Args:
            start_search: Starting datetime to search from
            duration_min: Required duration in minutes
            search_window_hours: How many hours to search ahead

        Returns:
            Dictionary with status and next_available datetime
        """
        # Check if starting slot is available
        result = self.check_slot_availability(start_search, duration_min)

        if result["status"] == "available":
            return {
                "status": "available",
                "next_available": start_search,
                "candidates": [],
            }

        # If conflict, return first suggested alternative
        if result["candidates"]:
            return {
                "status": "available",
                "next_available": result["candidates"][0],
                "candidates": result["candidates"][1:],
            }

        # Fallback: suggest slot 1 hour later
        return {
            "status": "available",
            "next_available": start_search + timedelta(hours=1),
            "candidates": [],
        }
