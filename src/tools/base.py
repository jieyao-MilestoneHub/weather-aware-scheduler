"""Abstract base classes for weather and calendar tools."""

from abc import ABC, abstractmethod
from datetime import datetime as dt_type

from src.models.entities import CalendarEvent, WeatherCondition


class WeatherTool(ABC):
    """Abstract base class for weather forecast tools.

    Implementations can be mock (deterministic) or real API-based (MCP).
    """

    @abstractmethod
    def get_forecast(self, city: str, dt: dt_type) -> WeatherCondition:
        """Get weather forecast for a specific city and datetime.

        Args:
            city: City name (e.g., "Taipei", "New York")
            dt: Target datetime (timezone-aware preferred)

        Returns:
            WeatherCondition with rain probability and risk categorization

        Raises:
            WeatherServiceError: If service is unavailable (triggers retry logic)
        """
        pass


class CalendarTool(ABC):
    """Abstract base class for calendar operations.

    Implementations can be mock (deterministic) or real API-based (MCP).
    """

    @abstractmethod
    def check_slot_availability(self, dt: dt_type, duration_min: int) -> dict:
        """Check if requested time slot is available.

        Args:
            dt: Requested datetime
            duration_min: Event duration in minutes

        Returns:
            Dictionary with structure:
            {
                "status": "available" | "conflict",
                "conflict_details": {...},  # if status="conflict"
                "next_available": datetime,  # next free slot
                "candidates": [datetime, datetime, datetime]  # top 3 alternatives
            }

        Raises:
            CalendarServiceError: If service is unavailable (triggers retry logic)
        """
        pass

    @abstractmethod
    def find_free_slot(
        self,
        start_search: dt_type,
        duration_min: int,
        search_window_hours: int = 8
    ) -> dict:
        """Find the next available free slot within search window.

        Args:
            start_search: Start of search window
            duration_min: Required duration in minutes
            search_window_hours: How many hours to search

        Returns:
            Dictionary with structure:
            {
                "status": "available" | "conflict",
                "conflict_details": dict | None,
                "next_available": datetime | None,
                "candidates": list[datetime]
            }

        Raises:
            CalendarServiceError: If service is unavailable (triggers retry logic)
        """
        pass

    @abstractmethod
    def create_event(
        self,
        *,
        city: str,
        dt: dt_type,
        duration_min: int,
        attendees: list[str],
        notes: str | None = None
    ) -> CalendarEvent:
        """Create a calendar event.

        Args:
            city: Event location
            dt: Event start time
            duration_min: Duration in minutes
            attendees: List of attendee names
            notes: Optional notes (weather warnings, adjustments, etc.)

        Returns:
            CalendarEvent with event_id and confirmation details

        Raises:
            CalendarServiceError: If service is unavailable (triggers retry logic)
        """
        pass


class WeatherServiceError(Exception):
    """Raised when weather service is unavailable or fails."""
    pass


class CalendarServiceError(Exception):
    """Raised when calendar service is unavailable or fails."""
    pass
