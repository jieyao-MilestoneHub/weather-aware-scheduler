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
        # Predefined conflict: Friday 15:00-15:30 (Oct 17, 2025)
        # This conflicts with rainy window (14:00-16:00) for integration tests
        self.blocked_slots = [
            {"weekday": 4, "hour": 15, "minute": 0, "duration": 30}  # Friday 15:00
        ]

    def check_slot_availability(self, dt: dt_type, duration_min: int) -> dict:
        """Check if requested time slot is available (original method for nodes.py).

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

    def check_conflicts(self, dt: dt_type, duration_min: int) -> list[dict]:
        """Check for conflicts at a specific time.

        Args:
            dt: Requested datetime
            duration_min: Event duration in minutes

        Returns:
            List of conflicting events (empty if no conflicts)
        """
        if self.raise_on_error:
            raise CalendarServiceError("Mock calendar service unavailable")

        conflicts = []

        for slot in self.blocked_slots:
            # Check if requested time overlaps with blocked slot
            slot_start_hour = slot["hour"]
            slot_start_minute = slot["minute"]
            slot_duration = slot["duration"]

            # Does the requested time overlap?
            if dt.weekday() == slot["weekday"]:
                # Calculate if times overlap
                req_start_minutes = dt.hour * 60 + dt.minute
                req_end_minutes = req_start_minutes + duration_min

                slot_start_minutes = slot_start_hour * 60 + slot_start_minute
                slot_end_minutes = slot_start_minutes + slot_duration

                # Check overlap: start before slot ends AND end after slot starts
                if req_start_minutes < slot_end_minutes and req_end_minutes > slot_start_minutes:
                    conflicts.append({
                        "start": dt.replace(hour=slot_start_hour, minute=slot_start_minute),
                        "end": dt.replace(hour=slot_start_hour, minute=slot_start_minute) + timedelta(minutes=slot_duration),
                        "summary": "Existing meeting"
                    })

        return conflicts

    def find_free_slot(
        self,
        start_search: dt_type,
        duration_min: int,
        search_window_hours: int = 8
    ) -> dt_type | None:
        """Find the next available free slot within search window.

        Args:
            start_search: Start of search window
            duration_min: Required duration in minutes
            search_window_hours: How many hours to search

        Returns:
            Next available datetime, or None if none found
        """
        if self.raise_on_error:
            raise CalendarServiceError("Mock calendar service unavailable")

        # Search in 30-minute increments
        current = start_search
        end_search = start_search + timedelta(hours=search_window_hours)

        while current < end_search:
            conflicts = self.check_conflicts(current, duration_min)
            if not conflicts:
                return current

            # Move to next 30-minute slot
            current += timedelta(minutes=30)

        return None

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
