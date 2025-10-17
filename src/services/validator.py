"""Slot validation logic."""
from datetime import datetime
from src.models.entities import Slot


class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass


def validate_slot(slot: Slot) -> bool:
    """
    Validate slot data meets requirements.
    
    Rules:
    - City must be non-empty string
    - Datetime must be in the future
    - Duration must be 5-480 minutes (5 min to 8 hours)
    
    Args:
        slot: Slot object to validate
    
    Returns:
        True if valid
    
    Raises:
        ValidationError: If validation fails with specific message
    
    Examples:
        >>> slot = Slot(city="Taipei", datetime=future_dt, duration=60, attendees=["Alice"])
        >>> validate_slot(slot)
        True
    """
    # Validate city
    if not slot.city or not slot.city.strip():
        raise ValidationError("City cannot be empty. Please provide a location.")
    
    # Validate datetime is in future
    now = datetime.now()
    if slot.datetime < now:
        raise ValidationError(
            f"Cannot schedule in the past. "
            f"Requested time: {slot.datetime.strftime('%Y-%m-%d %H:%M')}, "
            f"Current time: {now.strftime('%Y-%m-%d %H:%M')}"
        )
    
    # Validate duration (5-480 minutes)
    if slot.duration < 5 or slot.duration > 480:
        raise ValidationError(
            f"Duration must be between 5 and 480 minutes (5 min to 8 hours). "
            f"Provided: {slot.duration} minutes"
        )
    
    return True
