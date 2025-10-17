"""Unit tests for time utility functions."""
import pytest
from datetime import datetime
from hypothesis import given, strategies as st
from freezegun import freeze_time
from src.services.time_utils import parse_relative_time


class TestTimeOfDayParsing:
    """Test time-of-day keyword parsing."""
    
    @freeze_time("2025-10-13 10:00:00")
    def test_afternoon_resolves_to_14_00(self):
        """'afternoon' should resolve to 14:00 (2pm)."""
        result = parse_relative_time("Friday afternoon")
        assert result.hour == 14
        assert result.minute == 0
    
    @freeze_time("2025-10-13 10:00:00")
    def test_morning_resolves_to_09_00(self):
        """'morning' should resolve to 09:00 (9am)."""
        result = parse_relative_time("Friday morning")
        assert result.hour == 9
        assert result.minute == 0
    
    @freeze_time("2025-10-13 10:00:00")
    def test_evening_resolves_to_18_00(self):
        """'evening' should resolve to 18:00 (6pm)."""
        result = parse_relative_time("Friday evening")
        assert result.hour == 18
        assert result.minute == 0


class TestRelativeDayParsing:
    """Test relative day reference parsing."""
    
    @freeze_time("2025-10-13 10:00:00")  # Monday
    def test_friday_returns_next_friday(self):
        """'Friday' from Monday should return next Friday."""
        result = parse_relative_time("Friday 2pm")
        assert result.strftime("%A") == "Friday"
        assert result.day == 17  # Oct 17, 2025
    
    @freeze_time("2025-10-13 10:00:00")
    def test_tomorrow_returns_next_day(self):
        """'tomorrow' should return current date + 1."""
        result = parse_relative_time("tomorrow 2pm")
        assert result.day == 14  # Oct 14, 2025
    
    @freeze_time("2025-10-13 10:00:00")
    def test_today_returns_current_day(self):
        """'today' should return current date."""
        result = parse_relative_time("today 2pm")
        assert result.day == 13  # Oct 13, 2025


class TestPropertyBasedParsing:
    """Property-based tests for datetime parsing round-trips."""
    
    @given(st.datetimes(
        min_value=datetime(2025, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    def test_parse_format_roundtrip(self, dt: datetime):
        """Parsing a formatted datetime should return equivalent datetime."""
        # Format: "YYYY-MM-DD HH:MM"
        formatted = dt.strftime("%Y-%m-%d %H:%M")
        parsed = parse_relative_time(formatted)
        
        # Compare up to minute precision (ignore seconds/microseconds)
        assert parsed.year == dt.year
        assert parsed.month == dt.month
        assert parsed.day == dt.day
        assert parsed.hour == dt.hour
        assert parsed.minute == dt.minute


class TestExplicitTimeParsing:
    """Test explicit time format parsing."""
    
    def test_2pm_format_parses_correctly(self):
        """'2pm' should parse to 14:00."""
        result = parse_relative_time("Friday 2pm")
        assert result.hour == 14
        assert result.minute == 0
    
    def test_14_00_format_parses_correctly(self):
        """'14:00' should parse to 14:00."""
        result = parse_relative_time("Friday 14:00")
        assert result.hour == 14
        assert result.minute == 0
    
    def test_2_30pm_format_parses_correctly(self):
        """'2:30pm' should parse to 14:30."""
        result = parse_relative_time("Friday 2:30pm")
        assert result.hour == 14
        assert result.minute == 30
