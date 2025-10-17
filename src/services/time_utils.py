"""Time utility functions for parsing relative dates and times."""
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo


# Time of day mappings
TIME_OF_DAY_MAP = {
    'morning': (9, 0),
    'afternoon': (14, 0),
    'evening': (18, 0),
}


def parse_relative_time(text: str) -> datetime:
    """
    Parse relative time references into datetime objects.
    
    Supports:
    - Day names: "Friday", "Monday"
    - Relative: "tomorrow", "today", "next week"
    - Time of day: "afternoon" (14:00), "morning" (09:00), "evening" (18:00)
    - Explicit times: "2pm", "14:00", "2:30pm"
    
    Args:
        text: Input text containing date/time references
    
    Returns:
        datetime object in local timezone
    
    Examples:
        >>> parse_relative_time("Friday 2pm")
        datetime(2025, 10, 17, 14, 0)  # Next Friday at 2pm
        
        >>> parse_relative_time("tomorrow afternoon")
        datetime(2025, 10, 14, 14, 0)  # Tomorrow at 2pm
    """
    text_lower = text.lower()
    now = datetime.now()
    
    # Extract time of day or explicit time
    hour, minute = _extract_time(text_lower)
    
    # Extract date
    target_date = _extract_date(text_lower, now)
    
    # Combine date and time
    result = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    return result


def _extract_time(text: str) -> tuple[int, int]:
    """Extract hour and minute from text."""
    # Check for time of day keywords
    for keyword, (hour, minute) in TIME_OF_DAY_MAP.items():
        if keyword in text:
            return hour, minute
    
    # Check for explicit time patterns
    # Pattern 1: "2pm", "2:30pm", "14:00"
    time_pattern = re.compile(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', re.IGNORECASE)
    match = time_pattern.search(text)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).lower() if match.group(3) else None
        
        # Convert to 24-hour format
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        return hour, minute
    
    # Default to 2pm if no time specified
    return 14, 0


def _extract_date(text: str, now: datetime) -> datetime:
    """Extract date from text, handling relative references."""
    # Handle "today"
    if 'today' in text:
        return now
    
    # Handle "tomorrow"
    if 'tomorrow' in text:
        return now + timedelta(days=1)
    
    # Handle day names (Monday, Tuesday, etc.)
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days_of_week):
        if day in text:
            return _next_weekday(now, i)
    
    # Handle "next week"
    if 'next week' in text:
        # Look for day name after "next week"
        for i, day in enumerate(days_of_week):
            if day in text:
                return _next_weekday(now + timedelta(weeks=1), i)
        return now + timedelta(weeks=1)
    
    # Try to parse as absolute date
    try:
        # Look for date patterns like "2025-10-17" or "October 17"
        parsed = date_parser.parse(text, fuzzy=True, default=now)
        return parsed
    except:
        # Default to today
        return now


def _next_weekday(current: datetime, target_weekday: int) -> datetime:
    """
    Get the next occurrence of a specific weekday.
    
    Args:
        current: Current datetime
        target_weekday: Target day (0=Monday, 6=Sunday)
    
    Returns:
        datetime of next occurrence of target weekday
    """
    current_weekday = current.weekday()
    days_ahead = target_weekday - current_weekday
    
    # If target day is today or earlier this week, get next week's occurrence
    if days_ahead <= 0:
        days_ahead += 7
    
    return current + timedelta(days=days_ahead)
