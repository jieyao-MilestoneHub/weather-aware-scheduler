"""Unit tests for natural language parser."""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.services.parser import parse_natural_language, ParseError
from src.models.entities import Slot


class TestRelativeDateParsing:
    """Test relative date reference parsing."""
    
    @freeze_time("2025-10-13 10:00:00")  # Monday
    def test_parse_friday_returns_next_friday(self):
        """Friday should resolve to next Friday from current date."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 60min")
        assert result.datetime.strftime("%A") == "Friday"
        assert result.datetime.day == 17  # Oct 17, 2025 is Friday
    
    @freeze_time("2025-10-13 10:00:00")
    def test_parse_tomorrow_returns_next_day(self):
        """Tomorrow should resolve to current date + 1 day."""
        result = parse_natural_language("tomorrow 2pm Taipei meet Alice 60min")
        expected_date = datetime(2025, 10, 14)  # Oct 14
        assert result.datetime.date() == expected_date.date()
    
    @freeze_time("2025-10-13 10:00:00")
    def test_parse_next_week_returns_week_ahead(self):
        """Next week should resolve to 7 days from now."""
        result = parse_natural_language("next week Monday 2pm Taipei meet Alice 60min")
        expected_date = datetime(2025, 10, 20)  # Next Monday
        assert result.datetime.date() == expected_date.date()


class TestDurationParsing:
    """Test duration format parsing."""
    
    def test_parse_60min_returns_60_minutes(self):
        """'60min' should parse to 60 minutes."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 60min")
        assert result.duration == 60
    
    def test_parse_1_hour_returns_60_minutes(self):
        """'1 hour' should parse to 60 minutes."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 1 hour")
        assert result.duration == 60
    
    def test_parse_90_minutes_returns_90_minutes(self):
        """'90 minutes' should parse to 90 minutes."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 90 minutes")
        assert result.duration == 90
    
    def test_parse_1point5_hours_returns_90_minutes(self):
        """'1.5 hours' should parse to 90 minutes."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 1.5 hours")
        assert result.duration == 90


class TestAttendeeExtraction:
    """Test attendee name extraction."""
    
    def test_single_attendee_extracted(self):
        """Single attendee name should be extracted."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice 60min")
        assert "Alice" in result.attendees
    
    def test_multiple_attendees_with_and(self):
        """'meet Alice and Bob' should extract both names."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice and Bob 60min")
        assert "Alice" in result.attendees
        assert "Bob" in result.attendees
        assert len(result.attendees) == 2
    
    def test_multiple_attendees_with_comma(self):
        """'meet Alice, Bob, Charlie' should extract all names."""
        result = parse_natural_language("Friday 2pm Taipei meet Alice, Bob, Charlie 60min")
        assert set(result.attendees) == {"Alice", "Bob", "Charlie"}


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_invalid_date_february_30_raises_error(self):
        """Invalid dates like Feb 30 should raise ParseError."""
        with pytest.raises(ParseError, match="Invalid date"):
            parse_natural_language("February 30 2pm Taipei meet Alice 60min")
    
    @freeze_time("2025-10-13 10:00:00")
    def test_past_date_raises_error(self):
        """Past dates should raise ParseError."""
        with pytest.raises(ParseError, match="past"):
            parse_natural_language("October 10 2pm Taipei meet Alice 60min")  # 3 days ago
    
    def test_ambiguous_time_afternoon_defaults_to_2pm(self):
        """'afternoon' without specific time should default to 14:00."""
        result = parse_natural_language("Friday afternoon Taipei meet Alice 60min")
        assert result.datetime.hour == 14
        assert result.datetime.minute == 0
