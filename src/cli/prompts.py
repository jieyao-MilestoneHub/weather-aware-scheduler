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
