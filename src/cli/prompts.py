"""User-facing message templates for CLI."""

# Success messages
SUCCESS_TEMPLATE = """
✓ Event Created Successfully

{summary}

Reason: {reason}
{notes}
"""

# Error messages
ERROR_TEMPLATE = """
✗ Unable to Schedule Event

{error_message}

{guidance}
"""

# Clarification messages
CLARIFICATION_TEMPLATE = """
? Additional Information Needed

I have:
{extracted_info}

Please provide:
{missing_fields}

Example: "{example}"
"""

# Weather adjustment messages
WEATHER_ADJUSTED_TEMPLATE = """
⚠ Schedule Adjusted for Weather

{summary}

Reason: {reason}
Notes: {notes}
"""

# Conflict messages
CONFLICT_TEMPLATE = """
⚠ Time Conflict Detected

Requested time ({requested_time}) is already booked.

Alternative times available:
{alternatives}

Please select option (1-3) or provide different time.
"""

# Error guidance templates
MISSING_TIME_GUIDANCE = "Please provide time (e.g., '2pm', '14:00', 'afternoon')"
MISSING_LOCATION_GUIDANCE = "Please provide location (e.g., 'Taipei', 'New York')"
MISSING_DURATION_GUIDANCE = "Please provide duration (e.g., '60min', '1 hour') or default 60 minutes will be used"
INVALID_DATE_GUIDANCE = "Please provide valid date (e.g., 'Friday', 'tomorrow', '2025-10-17')"
PAST_DATE_GUIDANCE = "Cannot schedule in the past. Please provide future date/time."

# Service failure messages
WEATHER_SERVICE_FAILURE = "Weather information unavailable - manual weather check recommended"
CALENDAR_SERVICE_FAILURE = "Calendar service unavailable - manual conflict check recommended"

# Format example template (T087)
FORMAT_EXAMPLE_TEMPLATE = """
✗ Unable to Parse Request

Please provide a complete scheduling request with:

Required:
  • Date: Friday, tomorrow, next Monday, 2025-10-17
  • Time: 2pm, 14:00, afternoon (14:00), morning (09:00)
  • Location: Taipei, New York, Tokyo

Optional:
  • Duration: 60min, 1 hour, 90 minutes (default: 60 min)
  • Attendees: meet Alice, with Bob and Charlie

Examples:
  ✓ "Friday 2pm Taipei meet Alice 60min"
  ✓ "Tomorrow afternoon New York team sync 90 minutes"
  ✓ "Next Monday 10am Tokyo review meeting"

Try again with a complete request.
"""

# Clarification question templates with examples (T087)
TIME_CLARIFICATION = """
? Time information needed

What time should the meeting be?
  Examples:
    • "2pm" or "14:00"
    • "afternoon" (defaults to 2pm)
    • "morning" (defaults to 9am)
"""

LOCATION_CLARIFICATION = """
? Location information needed

Where should the meeting be?
  Examples:
    • "Taipei"
    • "New York"
    • "Tokyo"
"""

DURATION_CLARIFICATION = """
? Duration information needed (optional)

How long should the meeting be?
  Examples:
    • "60min" or "1 hour"
    • "90 minutes" or "1.5 hours"

  If not provided, defaults to 60 minutes.
"""

# One-shot clarification template (T087)
ONE_SHOT_CLARIFICATION_TEMPLATE = """
? Additional Details Needed

Current information:
{current_info}

Missing:
{missing_info}

Please provide the missing details in one response.
Example format: "{example_format}"
"""
