"""LangChain tool wrappers for Parser Agent.

Wraps existing parser service functions as tools that can be used by LLM agents.
"""

import logging
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.services.parser import (
    ParseError,
    _extract_attendees,
    _extract_city,
    _extract_datetime,
    _extract_description,
    _extract_duration,
    parse_natural_language,
)

logger = logging.getLogger(__name__)


# Pydantic schemas for tool inputs
class DateTimeExtractionInput(BaseModel):
    """Input for datetime extraction tool."""

    text: str = Field(..., description="Natural language text containing date and time information")


class LocationExtractionInput(BaseModel):
    """Input for location extraction tool."""

    text: str = Field(..., description="Text containing location/city name")


class AttendeesExtractionInput(BaseModel):
    """Input for attendees extraction tool."""

    text: str = Field(..., description="Text containing attendee names (e.g., 'meet Alice and Bob')")


class DurationExtractionInput(BaseModel):
    """Input for duration extraction tool."""

    text: str = Field(..., description="Text containing duration (e.g., '60 minutes', '1 hour')")


class CompletenessValidationInput(BaseModel):
    """Input for completeness validation tool."""

    extracted_data: dict[str, Any] = Field(
        ..., description="Dictionary with extracted scheduling information"
    )


# Tool definitions
@tool(args_schema=DateTimeExtractionInput)
def extract_datetime_tool(text: str) -> dict[str, Any]:
    """Extract date and time from natural language text.

    This tool parses relative time expressions like 'Friday 2pm', 'tomorrow afternoon',
    'next Monday at 10am' and converts them to absolute datetime objects.

    Args:
        text: Natural language text containing date/time information

    Returns:
        Dictionary with:
        - datetime_iso: ISO format datetime string
        - success: Whether extraction succeeded
        - error: Error message if failed
    """
    try:
        dt = _extract_datetime(text)
        logger.info(f"Extracted datetime: {dt.isoformat()} from text: '{text}'")
        return {
            "datetime_iso": dt.isoformat(),
            "datetime_str": dt.strftime("%Y-%m-%d %H:%M"),
            "success": True,
            "error": None,
        }
    except (ParseError, Exception) as e:
        logger.warning(f"Failed to extract datetime from '{text}': {e}")
        return {
            "datetime_iso": None,
            "datetime_str": None,
            "success": False,
            "error": str(e),
        }


@tool(args_schema=LocationExtractionInput)
def extract_location_tool(text: str) -> dict[str, Any]:
    """Extract location/city from text.

    Identifies city names from common cities or capitalized location names.

    Args:
        text: Text containing location information

    Returns:
        Dictionary with:
        - city: Extracted city name
        - success: Whether extraction succeeded
        - error: Error message if failed
    """
    try:
        city = _extract_city(text)
        logger.info(f"Extracted city: {city} from text: '{text}'")
        return {"city": city, "success": True, "error": None}
    except (ParseError, Exception) as e:
        logger.warning(f"Failed to extract city from '{text}': {e}")
        return {"city": None, "success": False, "error": str(e)}


@tool(args_schema=AttendeesExtractionInput)
def extract_attendees_tool(text: str) -> dict[str, Any]:
    """Extract attendee names from text.

    Parses patterns like 'meet Alice', 'meeting with Bob and Carol'.

    Args:
        text: Text containing attendee names

    Returns:
        Dictionary with:
        - attendees: List of attendee names
        - count: Number of attendees
        - success: Whether extraction succeeded
    """
    try:
        attendees = _extract_attendees(text)
        logger.info(f"Extracted {len(attendees)} attendees: {attendees} from text: '{text}'")
        return {
            "attendees": attendees,
            "count": len(attendees),
            "success": True,
            "error": None,
        }
    except Exception as e:
        logger.warning(f"Failed to extract attendees from '{text}': {e}")
        return {"attendees": [], "count": 0, "success": True, "error": None}


@tool(args_schema=DurationExtractionInput)
def extract_duration_tool(text: str) -> dict[str, Any]:
    """Extract meeting duration from text.

    Parses duration expressions like '60 minutes', '1 hour', '30 min'.

    Args:
        text: Text containing duration information

    Returns:
        Dictionary with:
        - duration_minutes: Duration in minutes
        - success: Whether extraction succeeded
        - error: Error message if failed
    """
    try:
        duration = _extract_duration(text)
        logger.info(f"Extracted duration: {duration} minutes from text: '{text}'")
        return {
            "duration_minutes": duration,
            "success": True,
            "error": None,
        }
    except (ParseError, Exception) as e:
        logger.warning(f"Failed to extract duration from '{text}': {e}")
        return {
            "duration_minutes": None,
            "success": False,
            "error": str(e),
        }


@tool(args_schema=CompletenessValidationInput)
def validate_completeness_tool(extracted_data: dict[str, Any]) -> dict[str, Any]:
    """Check if all required scheduling fields are present.

    Validates that datetime, location, and duration have been extracted.
    Attendees are optional.

    Args:
        extracted_data: Dictionary with extracted scheduling information

    Returns:
        Dictionary with:
        - is_complete: Whether all required fields are present
        - missing_fields: List of missing required fields
        - optional_missing: List of missing optional fields
    """
    required_fields = ["datetime_iso", "city", "duration_minutes"]
    optional_fields = ["attendees"]

    missing_required = []
    missing_optional = []

    # Check required fields
    for field in required_fields:
        if field not in extracted_data or extracted_data[field] is None:
            missing_required.append(field)

    # Check optional fields
    for field in optional_fields:
        if field not in extracted_data or not extracted_data[field]:
            missing_optional.append(field)

    is_complete = len(missing_required) == 0

    logger.info(
        f"Completeness check: is_complete={is_complete}, "
        f"missing_required={missing_required}, missing_optional={missing_optional}"
    )

    return {
        "is_complete": is_complete,
        "missing_fields": missing_required,
        "optional_missing": missing_optional,
        "has_all_required": is_complete,
    }


# Export all tools as a list for easy binding to agents
PARSER_TOOLS = [
    extract_datetime_tool,
    extract_location_tool,
    extract_attendees_tool,
    extract_duration_tool,
    validate_completeness_tool,
]
