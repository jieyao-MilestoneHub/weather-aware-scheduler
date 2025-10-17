"""Mock calendar tool with predefined conflicts for testing."""

import uuid
from datetime import datetime as dt_type, timedelta

from src.models.entities import CalendarEvent
from src.tools.base import CalendarTool, CalendarServiceError


class MockCalendarTool(CalendarTool):
    """Mock calendar tool with predefined conflicts.

    Deterministic logic for offline testing:
    - Friday 15:00 (30 min blocked) → conflict
    - Otherwise → available
    - Generates 3 candidate slots when conflict detected
    """

    def __init__(self, *, raise_on_error: bool = False):
        """Initialize mock calendar tool.

        Args:
            raise_on_error: If True, raise CalendarServiceError for testing
        """
        self.raise_on_error = raise_on_error
        # Predefined conflict: Friday 15:00, 30 minutes duration
        self.blocked_slots = [
            {"weekday": 4, "hour": 15, "minute": 0, "duration": 30}  # Friday 15:00
        ]

    def find_free_slot(self, dt: dt_type, duration_min: int) -> dict:
        """Check if requested time slot is available.

        Args:
            dt: Requested datetime
            duration_min: Event duration in minutes

        Returns:
            Dictionary with conflict status and alternatives

        Raises:
            CalendarServiceError: If raise_on_error=True
        """
        if self.raise_on_error:
            raise CalendarServiceError("Mock calendar service unavailable")

        # Check for conflicts with predefined blocked slots
        conflict_detected = False
        conflicting_slot = None

        for slot in self.blocked_slots:
            if (dt.weekday() == slot["weekday"] and
                dt.hour == slot["hour"] and
                dt.minute == slot["minute"]):
                conflict_detected = True
                conflicting_slot = slot
                break

        if conflict_detected:
            # Generate 3 candidate alternative slots
            candidates = self._generate_candidates(dt, duration_min)
            next_available = candidates[0] if candidates else dt + timedelta(hours=1)

            return {
                "status": "conflict",
                "conflict_details": {
                    "conflicting_event_id": "mock-conflict-001",
                    "conflicting_time": dt,
                    "duration": conflicting_slot["duration"]
                },
                "next_available": next_available,
                "candidates": candidates
            }

        # No conflict - slot is available
        return {
            "status": "available",
            "conflict_details": None,
            "next_available": dt,
            "candidates": []
        }

    def create_event(
        self,
        *,
        city: str,
        dt: dt_type,
        duration_min: int,
        attendees: list[str],
        notes: str | None = None
    ) -> CalendarEvent:
        """Create a mock calendar event.

        Args:
            city: Event location
            dt: Event start time
            duration_min: Duration in minutes
            attendees: List of attendee names
            notes: Optional notes

        Returns:
            CalendarEvent with mock event_id

        Raises:
            CalendarServiceError: If raise_on_error=True
        """
        if self.raise_on_error:
            raise CalendarServiceError("Mock calendar service unavailable")

        # Generate mock event ID
        event_id = f"mock-event-{uuid.uuid4().hex[:8]}"

        # Create event with confirmation
        return CalendarEvent(
            event_id=event_id,
            city=city,
            datetime=dt,
            duration=duration_min,
            attendees=attendees,
            reason="Event created successfully",
            notes=notes,
            status="confirmed"
        )

    def _generate_candidates(self, conflict_dt: dt_type, duration: int) -> list[dt_type]:
        """Generate 3 alternative time slots after conflict.

        Args:
            conflict_dt: Conflicting datetime
            duration: Required duration in minutes

        Returns:
            List of 3 candidate datetimes (30 min, 60 min, 120 min after conflict)
        """
        # Generate candidates at 30min, 60min, and 120min after conflict
        return [
            conflict_dt + timedelta(minutes=30),
            conflict_dt + timedelta(minutes=60),
            conflict_dt + timedelta(minutes=120)
        ]
