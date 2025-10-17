"""Unit tests for slot validation."""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from src.services.validator import validate_slot, ValidationError
from src.models.entities import Slot


class TestDatetimeValidation:
    """Test datetime validation rules."""
    
    @freeze_time("2025-10-13 10:00:00")
    def test_future_date_passes_validation(self):
        """Future datetime should pass validation."""
        future_dt = datetime(2025, 10, 20, 14, 0)
        slot = Slot(
            city="Taipei",
            datetime=future_dt,
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        assert validate_slot(slot) is True
    
    @freeze_time("2025-10-13 10:00:00")
    def test_past_date_fails_validation(self):
        """Past datetime should fail validation."""
        past_dt = datetime(2025, 10, 10, 14, 0)  # 3 days ago
        slot = Slot(
            city="Taipei",
            datetime=past_dt,
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        with pytest.raises(ValidationError, match="past"):
            validate_slot(slot)


class TestDurationValidation:
    """Test duration validation rules (5-480 minutes)."""
    
    def test_valid_duration_60_min_passes(self):
        """60 minutes (valid range) should pass."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        assert validate_slot(slot) is True
    
    def test_minimum_duration_5_min_passes(self):
        """5 minutes (boundary) should pass."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=5,
            attendees=["Alice"],
            description="meeting"
        )
        assert validate_slot(slot) is True
    
    def test_maximum_duration_480_min_passes(self):
        """480 minutes (8 hours boundary) should pass."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=480,
            attendees=["Alice"],
            description="meeting"
        )
        assert validate_slot(slot) is True
    
    def test_zero_duration_fails(self):
        """0 minutes should fail validation."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=0,
            attendees=["Alice"],
            description="meeting"
        )
        with pytest.raises(ValidationError, match="duration"):
            validate_slot(slot)
    
    def test_excessive_duration_1000_min_fails(self):
        """1000 minutes (>8 hours) should fail validation."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=1000,
            attendees=["Alice"],
            description="meeting"
        )
        with pytest.raises(ValidationError, match="duration"):
            validate_slot(slot)


class TestCityValidation:
    """Test city field validation."""
    
    def test_non_empty_city_passes(self):
        """Non-empty city string should pass."""
        slot = Slot(
            city="Taipei",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        assert validate_slot(slot) is True
    
    def test_empty_city_fails(self):
        """Empty city string should fail validation."""
        slot = Slot(
            city="",
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        with pytest.raises(ValidationError, match="city"):
            validate_slot(slot)
    
    def test_none_city_fails(self):
        """None as city should fail validation."""
        slot = Slot(
            city=None,
            datetime=datetime(2025, 10, 20, 14, 0),
            duration=60,
            attendees=["Alice"],
            description="meeting"
        )
        with pytest.raises(ValidationError, match="city"):
            validate_slot(slot)
