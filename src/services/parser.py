"""Natural language parser for schedule requests."""
import re
from datetime import datetime, timedelta
from typing import List
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
from src.models.entities import Slot
from src.services.time_utils import parse_relative_time


class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


# Common patterns
DURATION_PATTERN = re.compile(
    r'(\d+(?:\.\d+)?)\s*(min|mins|minute|minutes|hour|hours|h|hr|hrs)',
    re.IGNORECASE
)
ATTENDEE_PATTERN = re.compile(
    r'meet\s+([\w\s,]+?)(?:\s+(?:\d+|for|in|at|tomorrow|today|friday|monday|tuesday|wednesday|thursday|saturday|sunday))',
    re.IGNORECASE
)


def parse_natural_language(input_text: str) -> Slot:
    """
    Parse natural language scheduling request into structured Slot.

    Args:
        input_text: Natural language input (e.g., "Friday 2pm Taipei meet Alice 60min")

    Returns:
        Slot object with extracted fields

    Raises:
        ParseError: If parsing fails or required fields missing

    Examples:
        >>> parse_natural_language("Friday 14:00 Taipei meet Alice 60 min")
        Slot(city='Taipei', datetime=..., duration=60, attendees=['Alice'], ...)
    """
    if not input_text or not input_text.strip():
        raise ParseError("Input cannot be empty")

    input_text = input_text.strip()

    # Collect all parsing errors instead of failing immediately
    errors = []
    city = None
    dt = None
    duration = 60  # Default
    attendees = []
    description = ""

    # Try to extract city
    try:
        city = _extract_city(input_text)
    except ParseError as e:
        errors.append(str(e))

    # Try to extract datetime
    try:
        dt = _extract_datetime(input_text)
        # Check if this is a default/generic time (no explicit time reference in input)
        if not _has_explicit_time_reference(input_text):
            errors.append("Time/datetime not found in input. Please specify when (e.g., 'tomorrow 2pm', 'Friday 14:00').")
    except ParseError as e:
        errors.append(str(e))

    # If we have errors, raise combined error message
    if errors:
        raise ParseError(" ".join(errors))

    # Extract duration (optional, has default)
    duration = _extract_duration(input_text)

    # Extract attendees (optional)
    attendees = _extract_attendees(input_text)

    # Extract description (optional)
    description = _extract_description(input_text)

    return Slot(
        city=city,
        datetime=dt,
        duration=duration,
        attendees=attendees,
        description=description
    )


def _extract_city(text: str) -> str:
    """Extract city name from input text."""
    # Look for known cities or capitalize words (simple heuristic)
    # Common cities pattern
    cities = ['Taipei', 'Tokyo', 'New York', 'London', 'Paris', 'Berlin', 'Sydney']

    for city in cities:
        if city.lower() in text.lower():
            return city

    # Fallback: look for capitalized words, but exclude common person names after "meet" or "with"
    words = text.split()
    # First, identify words that are likely attendee names (after "meet" or "with")
    # Also mark "Meet"/"meet" itself as not a city
    attendee_indices = set()
    excluded_words = {'meet', 'with', 'meeting'}  # Words that are not cities

    for i, word in enumerate(words):
        if word.lower() in ['meet', 'with']:
            # Mark next capitalized words as potential attendees, not cities
            j = i + 1
            while j < len(words) and j < len(words) and len(words[j]) > 0 and words[j][0].isupper() and words[j].isalpha():
                attendee_indices.add(j)
                j += 1

    # Now look for capitalized words that are NOT attendee names or excluded words
    for i, word in enumerate(words):
        if i not in attendee_indices and word[0].isupper() and len(word) > 2 and words[i].isalpha():
            # Exclude day names, meeting words, and action verbs
            if word.lower() not in excluded_words | {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'tomorrow', 'today'}:
                return word

    raise ParseError("City/location not found in input. Please specify a location.")


def _has_explicit_time_reference(text: str) -> bool:
    """Check if input contains explicit time/date reference.

    Returns True if input has words like tomorrow, Friday, 2pm, etc.
    Returns False if input has no time reference (will use default).
    """
    time_keywords = [
        'tomorrow', 'today', 'tonight', 'morning', 'afternoon', 'evening', 'night',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'next', 'this', 'am', 'pm',
    ]

    text_lower = text.lower()

    # Check for time keywords
    if any(keyword in text_lower for keyword in time_keywords):
        return True

    # Check for time patterns like "2pm", "14:00", "2:30"
    import re
    time_patterns = [
        r'\d{1,2}:\d{2}',  # 14:00, 2:30
        r'\d{1,2}pm',      # 2pm, 14pm
        r'\d{1,2}am',      # 2am, 10am
        r'\d{4}-\d{2}-\d{2}',  # 2025-10-17
    ]

    for pattern in time_patterns:
        if re.search(pattern, text_lower):
            return True

    return False


def _extract_datetime(text: str) -> datetime:
    """Extract datetime from input text using time_utils."""
    try:
        return parse_relative_time(text)
    except Exception as e:
        raise ParseError(f"Unable to parse date/time from input: {str(e)}")


def _extract_duration(text: str) -> int:
    """Extract duration in minutes from input text."""
    match = DURATION_PATTERN.search(text)
    if not match:
        # Default to 60 minutes if not specified
        return 60
    
    amount = float(match.group(1))
    unit = match.group(2).lower()
    
    if unit in ['min', 'mins', 'minute', 'minutes']:
        return int(amount)
    elif unit in ['hour', 'hours', 'h', 'hr', 'hrs']:
        return int(amount * 60)
    
    return 60


def _extract_attendees(text: str) -> List[str]:
    """Extract attendee names from input text."""
    match = ATTENDEE_PATTERN.search(text)
    if not match:
        # Try simple heuristic: capitalized words after "meet" or "with"
        if 'meet' in text.lower() or 'with' in text.lower():
            words = text.split()
            for i, word in enumerate(words):
                if word.lower() in ['meet', 'with'] and i + 1 < len(words):
                    # Collect capitalized names
                    attendees = []
                    j = i + 1
                    while j < len(words):
                        if words[j][0].isupper() and words[j].isalpha():
                            attendees.append(words[j])
                            j += 1
                        else:
                            break
                    if attendees:
                        return attendees
        
        return ["Unknown"]
    
    # Parse attendees from match
    attendees_str = match.group(1).strip()
    
    # Split by 'and' or comma
    if ' and ' in attendees_str:
        attendees = [name.strip() for name in attendees_str.split(' and ')]
    elif ',' in attendees_str:
        attendees = [name.strip() for name in attendees_str.split(',')]
    else:
        attendees = [attendees_str.strip()]
    
    # Remove empty strings
    attendees = [a for a in attendees if a]
    
    return attendees if attendees else ["Unknown"]


def _extract_description(text: str) -> str:
    """Extract meeting description from input."""
    # Simple: use first part of text or context around "meet"
    if 'meet' in text.lower():
        return "meeting"
    elif 'coffee' in text.lower():
        return "coffee"
    elif 'lunch' in text.lower():
        return "lunch"
    elif 'sync' in text.lower():
        return "sync"
    else:
        return "event"
